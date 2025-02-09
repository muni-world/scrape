import logging
import time
import firebase_admin
from firebase_admin import credentials, firestore
from scrape.homepage import run_scrape
from scrape.deal_info import scrape_deal_info
from utils import initialize_driver, setup_logging

def main(should_download_os=True):
    """
    Main function to run the entire scraping process using a single Chrome instance and store deals in Firestore.
    
    Args:
        should_download_os (bool): If True, downloads OS files during scraping. Defaults to True.
    """
    setup_logging()
    logging.info(f"Starting scraping process (OS downloads: {'enabled' if should_download_os else 'disabled'})")
    
    # Check if the Firebase app is already initialized.
    # If not, initialize it with the service account credentials.
    try:
        firebase_admin.get_app()  # Try retrieving an existing Firebase app.
    except ValueError:
        # If no app is found, initialize using your service account key file.
        cred = credentials.Certificate("secrets/serviceAccountKey.json")  # Path to your service account key file
        firebase_admin.initialize_app(cred)
    
    # Use the Firestore client from firebase_admin,
    # which uses the credentials already loaded during Firebase app initialization.
    db = firestore.client()
    logging.info("Firestore client initialized using Firebase Admin SDK")
    
    # Initialize the Chrome webdriver only once
    driver = initialize_driver()
    
    try:
        # Use the homepage scraper to retrieve the deals.
        deals = run_scrape(driver)
        
        # If there are any deals, process each one.
        if deals:
            for deal in deals:
                try:
                    # Enrich each deal with additional details by scraping further information using the same driver.
                    additional_data = scrape_deal_info(deal["url"], driver, should_download_os=should_download_os)
                    deal.update(additional_data)
                    logging.info(f"Combined with additional data: {deal}")
                    
                    # Insert the enriched deal into the Firestore database.
                    doc_ref = db.collection("deals").document()  # Create a new document reference in the 'deals' collection.
                    doc_ref.set(deal)  # Populate the document with the deal data.
                    logging.info(f"Deal added to Firestore with ID: {doc_ref.id}")
                except Exception as e:
                    # Log any exception encountered while processing individual deals.
                    logging.error(f"Failed to scrape details for {deal}: {str(e)}")
                    continue
        else:
            logging.warning("No deals were retrieved")
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
    finally:
        logging.info("Scraping process completed")
        # Only wait if we're downloading OS files
        if should_download_os:
            time.sleep(5)  # Give downloads extra time to complete.
        driver.quit()  # Ensure the driver is properly closed.

# Run the main function when the script is executed.
if __name__ == "__main__":
    # You can modify this value to control OS downloads
    main(should_download_os=True)
