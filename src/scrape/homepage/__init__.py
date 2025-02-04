from ..utils import load_credentials, initialize_driver
import time

from s1_login import login
from s2_advanced_search import click_advanced_search
from s3_apply_filters import apply_filters
from s4_select_100 import select_100_deals
from s5_scrape_deals import scrape_deals

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
    keep_open = False

    try:
        # If no driver is provided, initialize a new one.
        if driver is None:
            driver = initialize_driver()
            own_driver = True
        
        email, password = load_credentials()
        driver.get("https://login.munios.com/")
        time.sleep(2)
        
        # Execute the scraping steps sequentially.
        login(driver, email, password)
        time.sleep(3)  # Give time for login to complete
        
        click_advanced_search(driver)
        time.sleep(3)  # Advanced search page loads
        
        apply_filters(driver)
        time.sleep(3)  # Filters applied
        
        select_100_deals(driver)
        time.sleep(1)  # Wait after selecting 100 deals
        
        deals = scrape_deals(driver)
        time.sleep(1)
        
        return deals

    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        keep_open = True
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        print("Keeping browser open for debugging...")
        time.sleep(300)  # Keep browser open for 5 minutes
        keep_open = True
    finally:
        # Only quit the driver if it was not passed in externally and we don't need to keep it open.
        if driver and own_driver and not keep_open:
            driver.quit()
        return deals

if __name__ == "__main__":
    run_scrape()