from .download_os import download_os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import initialize_driver
from clean_data import CompanyStandardizer
import logging

__all__ = ['scrape_deal_info']

def standardize_scraped_data(data: dict, standardizer: CompanyStandardizer) -> dict:
    """
    Standardizes all company names and websites in the scraped data.
    
    Args:
        data: Dictionary containing scraped company data
        standardizer: CompanyStandardizer instance
        
    Returns:
        dict: Data with standardized company names and original raw data
    """
    standardized = {
        "lead_managers": [],
        "co_managers": [],
        "municipal_advisors": [],
        "counsels": [],
        "os_file_path": data.get("os_file_path"),
        # Store all raw data in a nested dictionary
        "unprocessed_data": {
            "lead_managers": data["lead_managers"],
            "co_managers": data["co_managers"],
            "municipal_advisors": data["municipal_advisors"],
            "counsels": data["counsels"],
        },
    }
    
    # Standardize lead managers (from websites)
    for website in data["lead_managers"]:
        if canonical_name := standardizer.get_canonical_name_from_website(website):
            standardized["lead_managers"].append(canonical_name)
        else:
            logging.warning(f"Unknown lead manager website: {website}")
            standardized["lead_managers"].append(website)
    
    # Standardize co-managers (from names)
    for name in data["co_managers"]:
        if canonical_name := standardizer.get_canonical_name(name):
            standardized["co_managers"].append(canonical_name)
        else:
            logging.warning(f"Unknown co-manager name: {name}")
            standardized["co_managers"].append(name)
    
    # Standardize municipal advisors (from websites)
    for website in data["municipal_advisors"]:
        if canonical_name := standardizer.get_canonical_name_from_website(website):
            standardized["municipal_advisors"].append(canonical_name)
        else:
            logging.warning(f"Unknown municipal advisor website: {website}")
            standardized["municipal_advisors"].append(website)
    
    # Standardize counsels (from websites)
    for website in data["counsels"]:
        if canonical_name := standardizer.get_canonical_name_from_website(website):
            standardized["counsels"].append(canonical_name)
        else:
            logging.warning(f"Unknown counsel website: {website}")
            standardized["counsels"].append(website)
    
    return standardized

def scrape_deal_info(url, driver=None, standardizer=None):
    """
    Scrapes and standardizes deal information from a given URL.
    
    Args:
        url (str): The URL of the deal page to process
        driver (webdriver, optional): Selenium WebDriver instance to use
        standardizer (CompanyStandardizer, optional): Instance for name standardization
        
    Returns:
        dict: Standardized data containing lead managers, co-managers, etc.
    """
    own_driver = False
    if driver is None:
        driver = initialize_driver()
        own_driver = True

    if standardizer is None:
        standardizer = CompanyStandardizer()

    try:
        logging.info(f"Starting to scrape deal details from {url}")
        driver.get(url)
        
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Dictionary to store raw results
        raw_data = {
            "lead_managers": [],
            "co_managers": [],
            "municipal_advisors": [],
            "counsels": [],
        }

        def safe_get_links(class_name, section_name):
            try:
                section = driver.find_element(By.CLASS_NAME, class_name)
                links = section.find_elements(By.TAG_NAME, "a")
                return [link.get_attribute("href") for link in links]
            except Exception as e:
                logging.info(f"No {section_name} found: {str(e)}")
                return []

        # Get raw data
        raw_data["lead_managers"] = safe_get_links("lead", "lead managers")

        try:
            members_section = driver.find_element(By.CLASS_NAME, "members")
            members_text = members_section.find_element(By.CLASS_NAME, "logo").text
            raw_data["co_managers"] = [
                manager.strip().replace("•", "").strip() 
                for manager in members_text.split("\n")
            ]
        except Exception as e:
            logging.info(f"No co-managers found: {str(e)}")
            raw_data["co_managers"] = []

        raw_data["municipal_advisors"] = safe_get_links("ma", "municipal advisors")
        raw_data["counsels"] = safe_get_links("bc", "counsels")

        # Download OS
        os_file_path = download_os(driver)
        raw_data["os_file_path"] = os_file_path

        # Standardize the scraped data
        standardized_data = standardize_scraped_data(raw_data, standardizer)
        
        logging.info(f"Deal data standardized: {standardized_data}")
        return standardized_data

    except Exception as e:
        logging.error(f"Error scraping deal details: {str(e)}")
        return {}

    finally:
        if own_driver:
            driver.quit()
