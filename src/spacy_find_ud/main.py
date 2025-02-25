import firebase_admin
from firebase_admin import credentials, firestore
import logging
from find_underwriter_discount import extract_underwriting_discount_from_pdf
from overrides import overrides
import time

def process_pdf_discounts(reprocess_processed=True):
    """
    Processes Firestore documents to extract underwriting fee discounts from PDFs.
    
    This function iterates through the 'deals' collection in Firestore. For each document, 
    it checks whether the underwriting fee has been processed. If not (or if reprocessing is enabled), 
    it extracts the fee from the associated PDF, applies any manual overrides, and updates the document with the new fee.

    Args:
        reprocess_processed (bool): If True, documents with an existing fee will be reprocessed;
                                    if False, such documents are skipped.
    
    Returns:
        dict: A summary of processing results including counts of successes and failures.
    """
    # Configure logging with timestamp, level, and file output.
    logging.basicConfig(
        level=logging.INFO,
        filename="app.log",
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Initialize Firestore; if the client isn't initialized, load credentials and initialize.
    try:
        db = firestore.client()
    except ValueError:
        cred = credentials.Certificate("secrets/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    
    # Dictionary to track processing statistics and document statuses.
    results = {
        "total_documents": 0,
        "already_processed": 0,
        "missing_path": 0,
        "processing_failed": 0,
        "successfully_processed": 0,
        "failed_documents": [],
        "successful_documents": [],
    }

    def create_base_record(doc, path, os_type=None):
        """Creates a base record with common tracking fields from a document."""
        return {
            "doc_id": doc.id,
            "obligor": doc.to_dict().get("series_name_obligor", "Unknown"),
            "os_type": os_type,
            "path": path,
            "url": doc.to_dict().get("url", "N/A")
        }

    def create_failure_record(reason, **base_fields):
        """Creates a record representing a failed document processing attempt."""
        return {**base_fields, "reason": reason}

    def create_success_record(old_fee, new_fee, **base_fields):
        """Creates a record representing a successful fee extraction and update."""
        try:
            return {
                **base_fields,
                "pdf_path": base_fields.pop("path"),
                "old_fee": old_fee,
                "new_fee": new_fee,
                "multiple_fees": len(discount_result.get("scrape_breakdown", {}).get("amounts", [])) > 1 if discount_result else False,
                "had_override": base_fields["url"] in overrides if base_fields["url"] != "N/A" else False,
                "override_changes": base_fields.get("overridden_fields", {}),
                "amounts": discount_result.get("scrape_breakdown", {}).get("amounts", []),
            }
        except Exception as e:
            logging.error(f"Error creating success record for {doc.id}: {str(e)}")
            return None

    try:
        BATCH_SIZE = 50  # Process documents in batches of 50. Times out otherwise. 
        last_doc = None
        
        while True:
            # Retrieve the next batch of documents from the 'deals' collection.
            query = db.collection("deals").limit(BATCH_SIZE)
            if last_doc:
                query = query.start_after(last_doc)
                
            docs = query.stream()
            doc_list = list(docs)
            
            if not doc_list:
                break  # Exit loop if there are no more documents.

            for doc in doc_list:
                results["total_documents"] += 1
                deal_data = doc.to_dict()
                
                # Apply manual overrides if defined for the document's URL.
                url = deal_data.get("url", "N/A")
                override_changes = {}
                if url in overrides:
                    # Record the original field values before applying overrides.
                    override_changes = {field: deal_data.get(field, None)
                                        for field in overrides[url].keys()}
                    for field, new_value in overrides[url].items():
                        deal_data[field] = new_value
                    logging.warning(
                        f"Manual override applied for document {doc.id}\n"
                        f"URL: {url}\n"
                        f"File Path: {deal_data.get('os_file_path', 'N/A')}\n"
                        "Changed fields:\n" +
                        "\n".join([f"- {field}: {old_val} → {new_val}"
                                   for (field, old_val), new_val in zip(override_changes.items(), overrides[url].values())])
                    )
                    
                # Retrieve the document's OS type.
                os_type = deal_data.get("os_type")

                # Skip processing if the fee is already present and reprocessing is disabled.
                if deal_data.get("underwriters_fee_total") is not None:
                    if not reprocess_processed:
                        logging.info(f"Skipping processed document {doc.id}")
                        results["already_processed"] += 1
                        continue
                    else:
                        logging.info(f"Reprocessing document {doc.id} with existing fee: {deal_data['underwriters_fee_total']}")
                
                # Ensure the PDF path is available before attempting extraction.
                os_file_path = deal_data.get("os_file_path")
                if not os_file_path:
                    results["missing_path"] += 1
                    results["failed_documents"].append(create_failure_record(
                        reason="No PDF path found",
                        **create_base_record(doc, "Missing")
                    ))
                    logging.warning(f"Missing PDF path for document {doc.id} (URL: {deal_data.get('url', 'N/A')})")
                    continue
                
                try:
                    # Extract discount details from the PDF.
                    discount_result = extract_underwriting_discount_from_pdf(os_file_path)

                    if discount_result:
                        if isinstance(discount_result, dict) and "total" in discount_result:
                            discount_value = discount_result["total"]
                            # Log warning if multiple fee amounts are detected.
                            if len(discount_result.get("scrape_breakdown", {}).get("amounts", [])) > 1:
                                logging.warning(
                                    f"Multiple fee values found in document {doc.id}\n"
                                    f"File Path: {os_file_path}\n"
                                    f"Amounts: {discount_result['scrape_breakdown']['amounts']}\n"
                                    f"Using total: {discount_value}"
                                )
                        else:
                            logging.error(f"Unexpected return type from discount extraction for document {doc.id}: {type(discount_result)}")
                            results["processing_failed"] += 1
                            results["failed_documents"].append(create_failure_record(
                                reason=f"Unexpected return type: {type(discount_result)}",
                                **create_base_record(doc, os_file_path, os_type)
                            ))
                            continue

                        # Retrieve current fee value from the document.
                        old_value = deal_data.get("underwriters_fee_total")
                        
                        if old_value is not None and old_value != discount_value:
                            logging.info(
                                f"Updating fee for document {doc.id}\n"
                                f"File: {os_file_path}\n"
                                f"Old: {old_value} → New: {discount_value}"
                            )

                        # Prepare update payload with fee details and override info.
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
                        results["successful_documents"].append(create_success_record(
                            old_fee=old_value,
                            new_fee=discount_value,
                            **create_base_record(doc, os_file_path, os_type)
                        ))
                    else:
                        results["failed_documents"].append(create_failure_record(
                            reason="No discount found in PDF",
                            **create_base_record(doc, os_file_path, os_type)
                        ))
                        # Mark the document as having a scrape failure.
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
                    logging.error(
                        f"Error processing document {doc.id}\n"
                        f"Obligor: {deal_data.get('series_name_obligor', 'Unknown')}\n"
                        f"File Path: {os_file_path}\n"
                        f"OS Type: {os_type}\n"
                        f"Error: {str(e)}"
                    )
                    results["processing_failed"] += 1
                    continue
                
            # Set the last document for pagination.
            last_doc = doc_list[-1]
            logging.info(f"Processed batch up to document {last_doc.id}")
            
            # Attempt to refresh the Firestore connection.
            try:
                db = firestore.client()
            except Exception as e:
                logging.error(f"Connection refresh failed: {str(e)}")
                time.sleep(10)
                db = firestore.client()

        # Log the processing summary.
        logging.info("Processing complete. Summary:")
        for key, value in results.items():
            if key not in ["failed_documents", "successful_documents"]:
                logging.info(f"{key}: {value}")

        # Log detailed report of failed documents, grouped by OS type.
        if results["failed_documents"]:
            failures_by_type = {}
            for fail in results["failed_documents"]:
                os_type = fail.get("os_type", "Unknown")
                failures_by_type.setdefault(os_type, []).append(fail)

            logging.info("\nFailed Documents Report (Grouped by OS Type):")
            for os_type, failures in failures_by_type.items():
                logging.info(f"\n=== {os_type} ===")
                logging.info(f"Total Failures: {len(failures)}")
                for idx, fail in enumerate(failures, 1):
                    logging.info(f"\n  {idx}. Document ID: {fail['doc_id']}")
                    logging.info(f"     Path: {fail['path']}")
                    logging.info(f"     Obligor: {fail['obligor']}")
                    logging.info(f"     URL: {fail['url']}")
                    logging.info(f"     Reason: {fail['reason']}")
                logging.info("")

        # Log summary for documents with multiple fees and applied overrides.
        if results["successfully_processed"] > 0:
            try:
                multiple_fees_docs = [d for d in results["successful_documents"] if d and d.get("multiple_fees")]
                if multiple_fees_docs:
                    logging.info("\nDocuments with Multiple Fee Values:")
                    for idx, doc in enumerate(multiple_fees_docs, 1):
                        if not doc:
                            continue
                        logging.info(f"\n{idx}. Document ID: {doc.get('doc_id', 'N/A')}")
                        logging.info(f"   Obligor: {doc.get('obligor', 'N/A')}")
                        logging.info(f"   File: {doc.get('pdf_path', 'N/A')}")
                        logging.info(f"   URL: {doc.get('url', 'N/A')}")
                        logging.info(f"   Fee Values: {doc.get('amounts', [])}")
                        logging.info(f"   Total Fee Used: {doc.get('new_fee', 'N/A')}")
                        logging.info("")
            except Exception as e:
                logging.error(f"Error logging multiple fee details: {str(e)}")
            
            try:
                override_summary = {}
                for doc in results["successful_documents"]:
                    if doc.get("had_override"):
                        url = doc.get("url", "N/A")
                        if url not in override_summary:
                            override_summary[url] = {"count": 0, "docs": [], "changes": set()}
                        override_summary[url]["count"] += 1
                        override_summary[url]["docs"].append({
                            "doc_id": doc["doc_id"],
                            "obligor": doc["obligor"],
                            "changes": doc.get("override_changes", {}),
                        })
                        override_summary[url]["changes"].update(doc.get("override_changes", {}).keys())

                if override_summary:
                    logging.info("\nOverride Summary:")
                    for url, data in override_summary.items():
                        logging.info(f"\nURL: {url}")
                        logging.info(f"Total documents affected: {data['count']}")
                        logging.info(f"Modified fields: {', '.join(data['changes'])}")
                        logging.info("Affected documents:")
                        for doc in data["docs"]:
                            logging.info(f"  - {doc['doc_id']} ({doc['obligor']})")
                            logging.info(f"    Changes: {doc['changes']}")
                        logging.info("")
            except Exception as e:
                logging.error(f"Error generating override summary: {str(e)}")

        return results
        
    except Exception as e:
        # In case of a fatal error, log, wait briefly, and attempt reconnection.
        error_message = f"Fatal error: {str(e)}"
        logging.error(error_message)
        logging.info("Waiting 30 seconds before retrying...")
        time.sleep(30)
        try:
            db = firestore.client()
            logging.info("Reconnected to Firestore successfully")
        except Exception as retry_error:
            logging.error(f"Final connection failure: {str(retry_error)}")
        return results

def main():
    # Set the reprocessing switch; change as needed.
    REPROCESS_SWITCH = True
    results = process_pdf_discounts(reprocess_processed=REPROCESS_SWITCH)
    print("Processing complete. Summary:")
    for key, value in results.items():
        if key not in ["failed_documents", "successful_documents"]:
            print(f"{key}: {value}")

if __name__ == "__main__":
    main() 