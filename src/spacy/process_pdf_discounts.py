import firebase_admin
from firebase_admin import credentials, firestore
import logging
from find_underwriter_discount import extract_underwriting_discount_from_pdf

def process_pdf_discounts(reprocess_processed=True):
    """
    Cycles through Firestore deals collection to find and process PDFs that need underwriter fee extraction.
    
    For each document in the deals collection:
    1. Checks if underwriters_fee_total is null
    2. If null and os_file_path exists, processes the PDF
    3. Updates Firestore with extracted fee amount
    
    Args:
        reprocess_processed (bool): If True, re-process documents with existing fees.
                                  If False (default), skip already processed docs.
    
    Returns:
        dict: Summary of processing results with counts of successful/failed updates
    """
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Firestore with retry settings
    try:
        # Add retry settings to the client
        settings = firestore.ClientSettings(
            retry=firestore.RetrySettings(
                initial_delay=1.0,  # Start with 1 second delay
                maximum_delay=30.0,  # Max 30 seconds between retries
                multiplier=2.0,     # Double the delay each time
                max_attempts=5      # Try up to 5 times
            )
        )
        db = firestore.client(settings=settings)
    except ValueError:
        cred = credentials.Certificate("secrets/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client(settings=settings)
    
    # Initialize counters for summary and failed documents list
    results = {
        "total_documents": 0,
        "already_processed": 0,
        "missing_path": 0,
        "processing_failed": 0,
        "successfully_processed": 0,
        "failed_documents": [],  # New list to track failures
    }

    try:
        # Get all documents from deals collection
        deals_ref = db.collection("deals")
        docs = deals_ref.stream()
        
        for doc in docs:
            results["total_documents"] += 1
            deal_data = doc.to_dict()
            
            # Check if document has the correct os_type
            os_type = deal_data.get("os_type")
            if os_type not in ["OFFICIAL STATEMENT", "OFFERING MEMORANDUM"]:
                results["already_processed"] += 1
                # logging.info(f"Skipping document {doc.id} with os_type: {os_type}")
                continue

            # New skip logic ========================
            # Check if document is already processed
            if deal_data.get("underwriters_fee_total") is not None:
                if not reprocess_processed:  # If switch is OFF
                    logging.info(f"Skipping already processed document {doc.id}")
                    results["already_processed"] += 1
                    continue  # Jump to next document
                else:  # If switch is ON
                    logging.info(f"Reprocessing document {doc.id} with existing fee: {deal_data['underwriters_fee_total']}")
            # =======================================
            
            # Skip if no PDF path
            os_file_path = deal_data.get("os_file_path")
            if not os_file_path:
                results["missing_path"] += 1
                results["failed_documents"].append({
                    "doc_id": doc.id,
                    "path": "Missing",
                    "reason": "No PDF path found",
                    "obligor": deal_data.get("series_name_obligor", "Unknown"),
                })
                logging.warning(f"Missing PDF path for deal {doc.id}")
                continue
            
            try:
                # Extract discount from PDF, now returns a dict or None
                discount_result = extract_underwriting_discount_from_pdf(os_file_path)

                if discount_result:
                    # Check if discount_result is a dictionary and extract 'total'
                    if isinstance(discount_result, dict) and "total" in discount_result:
                        discount_value = discount_result["total"]
                    else:
                        # Handle unexpected return type (should be dict or None)
                        logging.error(f"Unexpected return type from extract_underwriting_discount_from_pdf for doc {doc.id}: {type(discount_result)}")
                        results["processing_failed"] += 1
                        results["failed_documents"].append({
                            "doc_id": doc.id,
                            "path": os_file_path,
                            "reason": f"Unexpected return type from discount extraction: {type(discount_result)}",
                            "obligor": deal_data.get("series_name_obligor", "Unknown"),
                        })
                        continue # Skip to the next document

                    # Get the old value before updating
                    old_value = deal_data.get("underwriters_fee_total")
                    
                    # Store the previous value before updating
                    doc.reference.update({
                        "previous_underwriters_fee_total": old_value,
                        "underwriters_fee_total": discount_value,
                        "underwriter_fee": discount_result,
                    })
                    results["successfully_processed"] += 1

                else:
                    # Enhanced logging with obligor name, file path, and os_type
                    results["failed_documents"].append({
                        "doc_id": doc.id,
                        "path": os_file_path,
                        "reason": "No discount found in PDF",
                        "obligor": deal_data.get("series_name_obligor", "Unknown"),
                        "os_type": os_type,  # Add os_type to the failure record
                    })
                    # Update document to indicate scrape failure
                    doc.reference.update({
                        "underwriter_fee": {
                            "total": None,
                            "scrape_success": False,
                        },
                    })
                    results["processing_failed"] += 1
                    
            except Exception as e:
                results["failed_documents"].append({
                    "doc_id": doc.id,
                    "path": os_file_path,
                    "reason": str(e),
                    "obligor": deal_data.get("series_name_obligor", "Unknown"),
                    "os_type": os_type,  # Add os_type to the error record
                })
                # Enhanced logging with obligor name, file path, and os_type
                logging.error(
                    f"Error processing deal {doc.id}\n"
                    f"Obligor: {deal_data.get('series_name_obligor', 'Unknown')}\n"
                    f"PDF Path: {os_file_path}\n"
                    f"OS Type: {os_type}\n"  # Add os_type to the error log
                    f"Error: {str(e)}"
                )
                results["processing_failed"] += 1
                continue
                
        # Log summary
        logging.info("Processing complete. Summary:")
        for key, value in results.items():
            if key != "failed_documents":  # Skip printing the failed documents list in summary
                logging.info(f"{key}: {value}")
        
        # Print failed documents report
        if results["failed_documents"]:
            logging.info("\nFailed Documents Report:")
            for idx, fail in enumerate(results["failed_documents"], 1):
                logging.info(f"\n{idx}. Document ID: {fail['doc_id']}")
                logging.info(f"   Path: {fail['path']}")
                logging.info(f"   Obligor: {fail['obligor']}")
                logging.info(f"   Reason: {fail['reason']}")

        # Add new section for changed documents
        if results["successfully_processed"] > 0:
            logging.info("\nChanged Documents Report:")
            for doc in docs:
                deal_data = doc.to_dict()
                if "underwriter_fee" in deal_data and deal_data["underwriter_fee"].get("scrape_success", False):
                    logging.info(f"\nDocument ID: {doc.id}")
                    logging.info(f"   Obligor: {deal_data.get('series_name_obligor', 'Unknown')}")
                    logging.info(f"   OS Type: {deal_data.get('os_type', 'Unknown')}")
                    logging.info(f"   PDF Path: {deal_data.get('os_file_path', 'Unknown')}")
                    logging.info(f"   Old Fee: {deal_data.get('previous_underwriters_fee_total', 'Unknown')}")
                    logging.info(f"   New Fee: {deal_data.get('underwriters_fee_total', 'Unknown')}")

        return results
        
    except Exception as e:
        logging.error(f"Fatal error in process_pdf_discounts: {str(e)}")
        return results

if __name__ == "__main__":
    # MANUAL SWITCH CONTROL
    # Set this to True to reprocess all documents (even processed ones)
    # Set to False to skip already processed documents (normal operation)
    REPROCESS_SWITCH = False  # ← Change this value manually
    
    process_pdf_discounts(reprocess_processed=REPROCESS_SWITCH) 