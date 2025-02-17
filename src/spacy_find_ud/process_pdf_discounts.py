import firebase_admin
from firebase_admin import credentials, firestore
import logging
from find_underwriter_discount import extract_underwriting_discount_from_pdf
from overrides import overrides
import time

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
    # Initialize logging - ADD FILE HANDLER
    logging.basicConfig(
        level=logging.INFO,
        filename="app.log",  # New: Log to file
        filemode="a",  # Append mode (creates file if not exists)
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Add timestamps
    )
    
    # Initialize Firestore
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
        "successful_documents": [],  # New list to track successes
    }

    def create_base_record(doc, path, os_type=None):
        """Factory for common document tracking fields"""
        return {
            "doc_id": doc.id,
            "obligor": doc.to_dict().get("series_name_obligor", "Unknown"),
            "os_type": os_type,
            "path": path,  # Unified field name used by both success/failure
            "url": doc.to_dict().get("url", "N/A")  # Add URL field
        }

    def create_failure_record(reason, **base_fields):
        """Extends base record with failure details"""
        return {**base_fields, "reason": reason}

    def create_success_record(old_fee, new_fee, **base_fields):
        """Extends base record with success details"""
        return {
            **base_fields,
            "pdf_path": base_fields.pop("path"),  # Rename to pdf_path
            "old_fee": old_fee,
            "new_fee": new_fee
        }

    try:
        # ========== BATCH PROCESSING ==========
        # keep getting '_UnaryStreamMultiCallable' object has no attribute '_retry' and seeinf this helps
        BATCH_SIZE = 50  # Process 50 documents at a time
        last_doc = None
        
        while True:
            # Get documents in batches
            query = db.collection("deals").limit(BATCH_SIZE)
            if last_doc:
                query = query.start_after(last_doc)
                
            docs = query.stream()
            doc_list = list(docs)
            
            if not doc_list:
                break  # Exit loop when no more documents

            for doc in doc_list:
                results["total_documents"] += 1
                deal_data = doc.to_dict()
                
                # ========== NEW OVERRIDE CHECK ==========
                # Like a librarian checking for special edition stickers on books
                url = deal_data.get("url", "N/A")
                override_changes = {}
                
                if url in overrides:
                    # Create record of original values before any changes
                    override_changes = {
                        field: deal_data.get(field, None)
                        for field in overrides[url].keys()
                    }
                    
                    # Apply overrides like temporary sticky notes
                    for field, new_value in overrides[url].items():
                        deal_data[field] = new_value
                # ========== END OVERRIDE CHECK ==========

                # Existing os_type check now uses potentially overridden value
                os_type = deal_data.get("os_type")
                if os_type not in ["OFFICIAL STATEMENT", "OFFERING MEMORANDUM"]:
                    results["already_processed"] += 1
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
                    results["failed_documents"].append(create_failure_record(
                        reason="No PDF path found",
                        **create_base_record(doc, "Missing")
                    ))
                    logging.warning(f"Missing PDF path for deal {doc.id} (URL: {deal_data.get('url', 'N/A')})")
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
                            results["failed_documents"].append(create_failure_record(
                                reason=f"Unexpected return type from discount extraction: {type(discount_result)}",
                                **create_base_record(doc, os_file_path, os_type)
                            ))
                            continue # Skip to the next document

                        # Get the old value before updating
                        old_value = deal_data.get("underwriters_fee_total")
                        
                        # Store the previous value before updating
                        update_data = {
                            "previous_underwriters_fee_total": old_value,
                            "underwriters_fee_total": discount_value,
                            "underwriter_fee": discount_result,
                            "unprocessed_pdf_scrape_before_override": {
                                "overridden_fields": override_changes,
                                "original_url": url
                            }
                        }

                        doc.reference.update(update_data)
                        results["successfully_processed"] += 1
                        # Track successful updates
                        results["successful_documents"].append(create_success_record(
                            old_fee=old_value,
                            new_fee=discount_value,
                            **create_base_record(doc, os_file_path, os_type)
                        ))

                    else:
                        # Enhanced logging with obligor name, file path, and os_type
                        results["failed_documents"].append(create_failure_record(
                            reason="No discount found in PDF",
                            **create_base_record(doc, os_file_path, os_type)
                        ))
                        # Update document to indicate scrape failure
                        doc.reference.update({
                            "underwriter_fee": {
                                "total": None,
                                "scrape_success": False,
                            },
                        })
                        results["processing_failed"] += 1
                        
                except Exception as e:
                    results["failed_documents"].append(create_failure_record(
                        reason=str(e),
                        **create_base_record(doc, os_file_path, os_type)
                    ))
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
                
            # Update last document for next batch
            last_doc = doc_list[-1]
            logging.info(f"Processed batch up to {last_doc.id}")
            
            # ========== CONNECTION REFRESH ==========
            # Like taking a quick break between grocery baskets
            try:
                db = firestore.client()  # Refresh connection
            except Exception as e:
                logging.error(f"Connection refresh failed: {str(e)}")
                # Wait 10 seconds before retrying
                time.sleep(10)
                db = firestore.client()  # Try again
        # ========== END BATCH PROCESSING ==========

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
                logging.info(f"   URL: {fail['url']}")  # Add URL logging
                logging.info(f"   Reason: {fail['reason']}")

        # Replace the existing "Changed Documents Report" section with:
        if results["successfully_processed"] > 0:
            logging.info("\nSuccessfully Processed Documents Report:")
            for idx, success in enumerate(results["successful_documents"], 1):
                logging.info(f"\n{idx}. Document ID: {success['doc_id']}")
                logging.info(f"   Obligor: {success['obligor']}")
                logging.info(f"   OS Type: {success['os_type']}")
                logging.info(f"   PDF Path: {success['pdf_path']}")
                logging.info(f"   URL: {success['url']}")  # Add URL logging
                logging.info(f"   Old Fee: {success['old_fee']}")
                logging.info(f"   New Fee: {success['new_fee']}")

        return results
        
    except Exception as e:
        # ========== ENHANCED ERROR HANDLING ==========
        # Like a cashier calling the manager when something breaks
        error_message = f"Fatal error: {str(e)}"
        logging.error(error_message)
        
        # Wait and retry once before giving up
        logging.info("Waiting 30 seconds and retrying...")
        time.sleep(30)
        try:
            db = firestore.client()  # Try to reconnect
            logging.info("Reconnected successfully")
        except Exception as retry_error:
            logging.error(f"Final connection failure: {str(retry_error)}")
        
        return results

if __name__ == "__main__":
    # MANUAL SWITCH CONTROL
    # Set this to True to reprocess all documents (even processed ones)
    # Set to False to skip already processed documents (normal operation)
    REPROCESS_SWITCH = True  # ← Change this value manually
    
    process_pdf_discounts(reprocess_processed=REPROCESS_SWITCH) 