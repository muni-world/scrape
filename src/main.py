from scrape.homepage import run_scrape
from scrape.deal_info import scrape_deal_info
from utils import initialize_driver, setup_logging
import logging


def main():
    """
    Main function to run the entire scraping process using a single Chrome instance.
    """
    setup_logging()
    logging.info("Starting scraping process")
    
    # Initialize the Chrome webdriver once.
    driver = initialize_driver()
    
    try:
        # Pass the single driver to the homepage scraper.
        deals = run_scrape(driver)
        
        # Check if any deals were retrieved.
        if deals:
            # Iterate through each deal and enrich with additional data,
            # reusing the same driver.
            for deal in deals:
                try:
                    additional_data = scrape_deal_info(deal["url"], driver)
                    deal.update(additional_data)
                    logging.info(f"Combined with additional data: {deal}")
                except Exception as e:
                    logging.error(f"Failed to scrape details for {deal}: {str(e)}")
                    continue

        else:
            logging.warning("No deals were retrieved")
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
    finally:
        logging.info("Scraping process completed")
        driver.quit()  # Close the driver once, at the very end.

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
