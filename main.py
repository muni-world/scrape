from scrape import run_scrape
import logging

def setup_logging():
    """
    Sets up basic logging configuration
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("scrape.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """
    Main function to run the entire scraping process
    """
    try:
        setup_logging()
        logging.info("Starting scraping process")
        
        # Run the scraping process
        deals = run_scrape()
        
        if deals:
            logging.info(f"Successfully retrieved {len(deals)} deals")
        else:
            logging.warning("No deals were retrieved")
            
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
    finally:
        logging.info("Scraping process completed")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
