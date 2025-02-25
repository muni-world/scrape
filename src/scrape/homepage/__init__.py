from .s1_login import login
from .s2_advanced_search import click_advanced_search
from .s3_apply_filters import apply_filters
from .s4_select_100 import select_100_deals
from .s5_paginate import paginate_and_scrape
from utils import load_muni_credentials, initialize_driver
import logging
from time import sleep


__all__ = ['run_scrape']

def run_scrape(driver=None):
    """
    Executes the complete scraping workflow for MuniOS healthcare deals.
    
    Args:
        driver (webdriver, optional): External WebDriver instance to use.
        
    Returns:
        list: Scraped deals data, or None if scraping fails.
    """
    own_driver = False
    deals = None

    try:
        if driver is None:
            driver = initialize_driver()
            own_driver = True
        
        email, password = load_muni_credentials()
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
        deals = paginate_and_scrape(driver, sector=SECTOR)

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