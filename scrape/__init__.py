from s1_login import login
from s2_advanced_search import click_advanced_search
from s3_apply_filters import apply_filters
from s4_scrape_filtered import scrape_filtered
# from .5_deals import get_deals
from utils import load_credentials, initialize_driver
import time

__all__ = ['run_scrape']

def run_scrape():
    """
    Main function to run all scraping steps in sequence.
    Keeps browser open on failure for debugging.
    """
    driver = None
    keep_open = False  # Flag to track if we should keep browser open
    
    try:
        # Step 1: Load credentials and initialize driver
        email, password = load_credentials()
        driver = initialize_driver()
        driver.get("https://login.munios.com/")
        time.sleep(5)  
        
        # Run scraping steps
        login(driver, email, password)
        time.sleep(5)  # Give time for login to complete
        
        click_advanced_search(driver)
        time.sleep(5)  # Wait for advanced search page to load
        
        apply_filters(driver)
        time.sleep(5)  # Wait for filters to be applied

        scrape_filtered(driver)
                
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        keep_open = True  # Keep browser open on Ctrl+C
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        print("Keeping browser open for debugging...")
        time.sleep(300)  # 5 minutes
        keep_open = True
    finally:
        # Only close the driver if we don't need to keep it open
        if driver and not keep_open:
            driver.quit()

if __name__ == "__main__":
    run_scrape()