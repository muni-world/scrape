import logging
import time
from scrape.homepage import run_scrape
from scrape.deal_info import scrape_deal_info
from scrape.emma_os import run_emma_os_scraper
from utils import initialize_driver, setup_logging, initialize_firestore

def main(should_scrape_deals=True, should_download_os=True, should_run_emma=True):
    """
    Main function to run the scraping process using a single Chrome instance and store deals in Firestore.
    
    Args:
        should_scrape_deals (bool): If True, scrapes and processes deals. Defaults to True.
        should_download_os (bool): If True, downloads OS files during deal scraping. Only works if should_scrape_deals is True. Defaults to True.
        should_run_emma (bool): If True, runs the emma_os_scraper. Defaults to True.
    """
    # Validate that should_download_os is only True when should_scrape_deals is True
    if should_download_os and not should_scrape_deals:
        logging.warning("should_download_os was set to True but should_scrape_deals is False. Must be true for OS downloads.")
        should_download_os = False

    setup_logging()
    logging.info(f"Starting scraping process with options: Deals: {should_scrape_deals}, OS downloads: {should_download_os}, Emma: {should_run_emma}")
    
    db = initialize_firestore()
    logging.info("Firestore client initialized using Firebase Admin SDK")
    
    # Initialize the Chrome webdriver only once
    driver = initialize_driver()
    
    try:
        # Only run deals scraping if enabled
        if should_scrape_deals:
            # Use the homepage scraper to retrieve the deals.
            deals = run_scrape(driver)
            
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
        
        # Only run emma_os_scraper if enabled
        if should_run_emma:
            run_emma_os_scraper(driver)

    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
    finally:
        logging.info("Scraping process completed")
        # Only wait if we're downloading OS files
        if should_download_os:
            time.sleep(5)  # slow down requests to avoid rate limiting
        driver.quit()  # Ensure the driver is properly closed.

# Run the main function when the script is executed.
if __name__ == "__main__":
    # You can easily control what runs by changing these parameters
    main(
        should_scrape_deals=True,   # Run deals scraping (munios homepage and deal info)
        should_download_os=False,    # Don't download OS files during deal scraping
        should_run_emma=False,       # Don't run emma_os_scraper
    )