from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep
import logging
from .s5_scrape_deals import scrape_deals

def paginate_and_scrape(driver, sector):
    """
    Handles pagination and scrapes deals from all available pages.
    
    Args:
        driver: Selenium WebDriver instance
        sector (str): Sector filter being used (e.g. 'HC')
    
    Returns:
        list: Combined list of dictionaries containing deal information from all pages
    """
    all_deals = []
    page_number = 1
    
    try:
        while True:
            logging.info(f"Scraping page {page_number}")
            
            # Scrape current page
            page_deals = scrape_deals(driver, sector)
            all_deals.extend(page_deals)
            
            # Check if pagination exists
            pagination_elements = driver.find_elements(By.CSS_SELECTOR, "ul.pagination")
            if not pagination_elements:
                logging.info("No pagination found - single page of results")
                break
            
            # Find pagination container
            try:
                pagination_ul = driver.find_element(By.CSS_SELECTOR, "ul.pagination")
                # Find all pagination links except the active one
                pagination_links = pagination_ul.find_elements(
                    By.CSS_SELECTOR, 
                    "li:not(.active) a[onclick*='pagination']"
                )
                
                # Find the next page number
                current_active = pagination_ul.find_element(By.CSS_SELECTOR, "li.active")
                current_page = int(current_active.text)
                next_page = current_page + 1
                
                # Look for the link to the next page
                next_link = None
                for link in pagination_links:
                    if f'pagination("{next_page}")' in link.get_attribute("onclick"):
                        next_link = link
                        break
                
                if next_link is None:
                    logging.info("No more pages to scrape")
                    break
                    
                # Click the next page
                driver.execute_script("arguments[0].click();", next_link)
                
                # Wait for the page to load
                sleep(3)  # Basic wait for page load
                
                page_number += 1
                
            except NoSuchElementException:
                logging.info("No pagination found or reached last page")
                break
                
            except Exception as e:
                logging.error(f"Error during pagination: {e}")
                break
    
    except Exception as e:
        logging.error(f"Fatal error during pagination: {e}")
    
    logging.info(f"Completed scraping {page_number} pages. Total deals found: {len(all_deals)}")
    return all_deals
