import firebase_admin
from firebase_admin import credentials, firestore
import logging
from find_underwriter_discount import extract_underwriting_discount_from_pdf

def process_pdf_discounts():
    """
    Cycles through Firestore deals collection to find and process PDFs that need underwriter fee extraction.
    
    For each document in the deals collection:
    1. Checks if underwriters_fee_total is null
    2. If null and os_file_path exists, processes the PDF
    3. Updates Firestore with extracted fee amount
    
    Returns:
        dict: Summary of processing results with counts of successful/failed updates
    """
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Firestore if not already initialized
    try:
        db = firestore.client()
    except ValueError:
        cred = credentials.Certificate("secrets/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    
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
            
            # Log if we're processing an already processed document
            if deal_data.get("underwriters_fee_total") is not None:
                logging.info(f"Reprocessing document {doc.id} with existing fee: {deal_data['underwriters_fee_total']}")
                results["already_processed"] += 1
            
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

                    # discount_value is already a float from extract_underwriting_discount_pdf
                    # No need to convert from string or remove '$' and ',' again here.

                    # Update Firestore document with the structured underwriter_fee data
                    doc.reference.update({
                        "underwriters_fee_total": discount_value,
                        "underwriter_fee": discount_result, # Store the entire dict
                    })

                    logging.info(f"Updated deal {doc.id} with fee: {discount_value}")
                    results["successfully_processed"] += 1

                else:
                    # Enhanced logging with obligor name and file path
                    results["failed_documents"].append({
                        "doc_id": doc.id,
                        "path": os_file_path,
                        "reason": "No discount found in PDF",
                        "obligor": deal_data.get("series_name_obligor", "Unknown"),
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
                })
                # Enhanced logging with obligor name and file path
                logging.error(
                    f"Error processing deal {doc.id}\n"
                    f"Obligor: {deal_data.get('series_name_obligor', 'Unknown')}\n"
                    f"PDF Path: {os_file_path}\n"
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
            
        return results
        
    except Exception as e:
        logging.error(f"Fatal error in process_pdf_discounts: {str(e)}")
        return results

if __name__ == "__main__":
    process_pdf_discounts() 