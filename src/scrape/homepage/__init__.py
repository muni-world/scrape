from .s1_login import login
from .s2_advanced_search import click_advanced_search
from .s3_apply_filters import apply_filters
from .s4_select_100 import select_100_deals
from .s5_scrape_deals import scrape_deals

from utils import load_credentials, initialize_driver
import logging
from time import sleep

__all__ = ['run_scrape']

def run_scrape(driver=None):


    """
    Main function to run all scraping steps in sequence.
    If a driver is provided, it will be used instead of initializing a new one.

    Args:
        driver (webdriver, optional): Selenium WebDriver instance to use.

    Returns:
        list: List of scraped deals, or None if scraping fails.
    """
    own_driver = False  # Indicate if this function owns the driver.
    deals = None

    try:
        # If no driver is provided, initialize a new one.
        if driver is None:
            driver = initialize_driver()
            own_driver = True
        
        email, password = load_credentials()
        driver.get("https://login.munios.com/")
        
        # Define configurable sector at start of process. This is the sector code for Healthcare. We can change this to other sectors if desired
        SECTOR = "HC"
        
        # Execute the scraping steps sequentially.
        login(driver, email, password)
        sleep(2)
        click_advanced_search(driver)
        sleep(3)
        apply_filters(driver, sector=SECTOR)      
        sleep(3)
        select_100_deals(driver)    
        sleep(2)
        deals = scrape_deals(driver, sector=SECTOR)
        

        return deals

    except Exception as e:
        logging.error(f"Homepage scraping failed: {str(e)}", exc_info=True)
    finally:
        # Only quit the driver if it was not passed in externally
        if driver and own_driver:
            driver.quit()
        return deals

if __name__ == "__main__":
    run_scrape()