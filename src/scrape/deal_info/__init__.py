from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import initialize_driver
import logging

__all__ = ['scrape_deal_info']

def scrape_deal_info(url, driver=None):

    """
    Scrapes deal information from a given URL including lead managers, co-managers,
    municipal advisors and counsels. All sections are treated as optional.
    
    Args:
        url (str): The URL of the deal page to process
        driver (webdriver, optional): Selenium WebDriver instance to use
        
    Returns:
        dict: Scraped data containing lead managers, co-managers, municipal advisors and counsels
    """
    own_driver = False
    if driver is None:
        driver = initialize_driver()
        own_driver = True


    try:
        # Log starting the scrape process
        logging.info(f"Starting to scrape deal details from {url}")
        driver.get(url)
        

        # Wait until the browser reports that the page is fully loaded.
        # This is more reliable than time.sleep since it waits only as long as needed.
        WebDriverWait(driver, 10).until(
          lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Dictionary to store results
        scraped_data = {
            "lead_managers": [],
            "co_managers": [],
            "municipal_advisors": [],
            "counsels": [],
        }

        # Helper function to safely retrieve links from an element
        def safe_get_links(class_name, section_name):
            try:
                section = driver.find_element(By.CLASS_NAME, class_name)
                links = section.find_elements(By.TAG_NAME, "a")
                return [link.get_attribute("href") for link in links]
            except Exception as e:
                logging.info(f"No {section_name} found: {str(e)}")
                return []


        # Get lead manager hrefs (optional)
        scraped_data["lead_managers"] = safe_get_links("lead", "lead managers")

        # Get co-manager text between BRs (optional)
        try:
            members_section = driver.find_element(By.CLASS_NAME, "members")
            members_text = members_section.find_element(By.CLASS_NAME, "logo").text
            scraped_data["co_managers"] = [
                manager.strip().replace("•", "").strip() 
                for manager in members_text.split("\n")
            ]
        except Exception as e:
            logging.info(f"No co-managers found: {str(e)}")
            scraped_data["co_managers"] = []


        # Get municipal advisor hrefs (optional)
        scraped_data["municipal_advisors"] = safe_get_links("ma", "municipal advisors")

        # Get counsel hrefs (optional)
        scraped_data["counsels"] = safe_get_links("bc", "counsels")

        logging.info(f"Additional deal data scraped: {scraped_data}")
        return scraped_data


    except Exception as e:
        logging.error(f"Error scraping deal details: {str(e)}")
        return {}
        

    finally:
        if own_driver:
            driver.quit()
