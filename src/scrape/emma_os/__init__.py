"""
This module connects to the Firestore 'deals' collection and processes each deal document.
For each document, it looks for a cusip link, fetches the corresponding EMMA page using Selenium,
scrapes out the Official Statement link, then updates the document with a new field "emma_os_url".

Usage:
  Set the RERUN_ALL flag to True to process every document (overwriting existing `emma_os_url` values).
  Otherwise, only documents without that field are processed.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import initialize_driver
import time
import logging
import random

# Setup logging to output to a file ("app.log") as well as to the console.
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s %(levelname)s: %(message)s",
  handlers=[
    logging.FileHandler("app.log"),
    logging.StreamHandler()
  ]
)

# When True, every document in the collection will be re-processed.
# When False, only documents without an "emma_os_url" field will be processed.
RERUN_ALL = False

# Initialize firebase_admin if not already initialized.
if not firebase_admin._apps:
    # Use the same service account approach as in main.py
    cred = credentials.Certificate("secrets/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

def handle_popups(driver):
  """
  Handles initial popup dialogs for privacy policy and terms of use.
  
  Args:
      driver: Selenium WebDriver instance
  """
  try:
    # Handle cookie/privacy policy popup
    time.sleep(5)
    cookie_button = WebDriverWait(driver, 5).until(
      EC.presence_of_element_located((By.ID, "acceptId"))
    )
    cookie_button.click()
    logging.info("Accepted privacy policy")

    # Handle terms of use popup
    terms_button = WebDriverWait(driver, 5).until(
      EC.presence_of_element_located((By.ID, "ctl00_mainContentArea_disclaimerContent_yesButton"))
    )
    terms_button.click()
    logging.info("Accepted terms of use")

  except Exception as e:
    logging.warning(f"Error handling popups: {str(e)}")
    # Continue execution even if popups aren't found/handled
    pass

def process_emma_page(driver, cusip_url):
  """
  Fetches and processes an EMMA page to extract the OS link.
  
  Args:
      driver: Selenium WebDriver instance
      cusip_url: URL of the EMMA page to process
      
  Returns:
      str: The extracted OS URL or None if not found
  """
  try:
    driver.get(cusip_url)
    
    # Handle popups before proceeding
    handle_popups(driver)
    
    # Wait for page load
    WebDriverWait(driver, 5).until(
      lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Check for error message first - moved outside of try block
    error_element = driver.find_element(By.CSS_SELECTOR, "div.error-content h4 span")
    if error_element and "no records exist for this CUSIP" in error_element.text:
      logging.info("No records exist for this CUSIP, skipping...")
      return None

    # Only try to find OS link if no error was found
    link_element = WebDriverWait(driver, 10).until(
      EC.presence_of_element_located((By.CSS_SELECTOR, "a[ga-name='ClickLinkOS']"))
    )
    
    href = link_element.get_attribute("href")
    if not href:
      return None

    # Ensure URL is complete
    if not (href.startswith("http://") or href.startswith("https://")):
      full_url = "https://emma.msrb.org" + href
    else:
      full_url = href

    return full_url

  except Exception as e:
    logging.error(f"Error processing EMMA page: {str(e)}")
    return None

def run_emma_os_scraper():
  """
  Runs the scraper for the Firestore 'deals' collection using Selenium.
  """
  success_count = 0
  failure_count = 0
  skipped_docs = []
  failed_docs = []
  driver = None
  BATCH_SIZE = 50  # Process 50 documents at a time
  
  try:
    # Initialize Selenium driver
    driver = initialize_driver()
    
    # Get initial Firestore client
    db = firestore.client()
    
    # Process documents in batches
    last_doc = None
    while True:
      try:
        # Get next batch of documents
        query = db.collection("deals").limit(BATCH_SIZE)
        if last_doc:
          query = query.start_after(last_doc)
          
        # Convert to list to avoid cursor timeout
        docs = list(query.stream())
        
        if not docs:
          break  # No more documents to process
          
        for doc in docs:
          doc_id = doc.id
          doc_data = doc.to_dict()
          logging.info(f"Processing document ID: {doc_id}")

          # Skip if already processed
          if not RERUN_ALL and "emma_os_url" in doc_data:
            logging.info(f"Document ID {doc_id} already has emma_os_url. Skipping.")
            continue

          # Extract cusip URL
          cusip_url = None
          if "cusip_links" in doc_data and isinstance(doc_data["cusip_links"], list) and doc_data["cusip_links"]:
            cusip_url = doc_data["cusip_links"][0]
          elif "cusip_link" in doc_data and isinstance(doc_data["cusip_link"], str) and doc_data["cusip_link"]:
            cusip_url = doc_data["cusip_link"]
          # Check for cusips map structure
          elif "cusips" in doc_data and isinstance(doc_data["cusips"], dict) and doc_data["cusips"]:
            # Get the first value from the cusips map
            cusip_url = next(iter(doc_data["cusips"].values()))

          if not cusip_url:
            logging.error(f"Document ID {doc_id}: No cusip link found")
            failed_docs.append({"doc_id": doc_id, "issue": "No cusip link found"})
            failure_count += 1
            continue

          # Process the EMMA page
          emma_os_url = process_emma_page(driver, cusip_url)
          
          if not emma_os_url:
            logging.info(f"Document ID {doc_id}: No OS URL found, skipping")
            # Collect relevant fields for investigation
            skip_info = {
              "doc_id": doc_id,
              "cusip_url": cusip_url,
              "os_file_path": doc_data.get("os_file_path"),
              "os_type": doc_data.get("os_type"),
              "series_name_obligor": doc_data.get("series_name_obligor"),
              "original_url": doc_data.get("unprocessed_pdf_scrape_before_override", {}).get("original_url"),
            }
            skipped_docs.append(skip_info)
            continue

          # Update Firestore
          doc.reference.update({"emma_os_url": emma_os_url})
          logging.info(f"Document ID {doc_id}: Successfully updated with emma_os_url: {emma_os_url}")
          success_count += 1

        # Update last document for next batch
        last_doc = docs[-1]
        
        # Refresh Firestore connection after each batch
        db = firestore.client()
        
        # Add small delay between batches
        time.sleep(2)
        
      except Exception as batch_error:
        logging.error(f"Error processing batch: {str(batch_error)}")
        # Wait longer on error before retrying
        time.sleep(10)
        try:
          # Attempt to refresh connection
          db = firestore.client()
        except Exception as refresh_error:
          logging.error(f"Failed to refresh connection: {str(refresh_error)}")
          raise  # Re-raise if we can't recover

    # Enhanced logging summary
    logging.info("\n=== SCRAPER SUMMARY ===")
    logging.info(f"Successfully processed: {success_count} documents")
    logging.info(f"Failed processing: {failure_count} documents")
    logging.info(f"Skipped (no OS URL): {len(skipped_docs)} documents")
    
    if failed_docs:
      logging.info("\n=== FAILED DOCUMENTS ===")
      for item in failed_docs:
        logging.info(f"\nDocument ID: {item['doc_id']}")
        logging.info(f"Issue: {item['issue']}")
        logging.info(f"URL: {item.get('url', 'N/A')}")

    if skipped_docs:
      logging.info("\n=== SKIPPED DOCUMENTS (No OS URL) ===")
      for item in skipped_docs:
        logging.info(f"\nDocument ID: {item['doc_id']}")
        logging.info(f"CUSIP URL: {item['cusip_url']}")
        logging.info(f"OS File Path: {item.get('os_file_path', 'N/A')}")
        logging.info(f"OS Type: {item.get('os_type', 'N/A')}")
        logging.info(f"Series Name/Obligor: {item.get('series_name_obligor', 'N/A')}")
        logging.info(f"Original URL: {item.get('original_url', 'N/A')}")

  except Exception as e:
    logging.error(f"Error in main scraper loop: {str(e)}")
  
  finally:
    if driver:
      driver.quit()

    # Enhanced logging summary
    logging.info("\n=== SCRAPER SUMMARY ===")
    logging.info(f"Successfully processed: {success_count} documents")
    logging.info(f"Failed processing: {failure_count} documents")
    logging.info(f"Skipped (no OS URL): {len(skipped_docs)} documents")
    
    if failed_docs:
      logging.info("\n=== FAILED DOCUMENTS ===")
      for item in failed_docs:
        logging.info(f"\nDocument ID: {item['doc_id']}")
        logging.info(f"Issue: {item['issue']}")
        logging.info(f"URL: {item.get('url', 'N/A')}")

    if skipped_docs:
      logging.info("\n=== SKIPPED DOCUMENTS (No OS URL) ===")
      for item in skipped_docs:
        logging.info(f"\nDocument ID: {item['doc_id']}")
        logging.info(f"CUSIP URL: {item['cusip_url']}")
        logging.info(f"OS File Path: {item.get('os_file_path', 'N/A')}")
        logging.info(f"OS Type: {item.get('os_type', 'N/A')}")
        logging.info(f"Series Name/Obligor: {item.get('series_name_obligor', 'N/A')}")
        logging.info(f"Original URL: {item.get('original_url', 'N/A')}")

if __name__ == "__main__":
  run_emma_os_scraper()
