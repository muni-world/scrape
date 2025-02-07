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
        data (dict): Dictionary containing scraped company data.
        standardizer (CompanyStandardizer): Instance to standardize company names.
        
    Returns:
        dict: Data with standardized company names and preserved original raw data.
    """
    # Verify required field "lead_managers" exists; if missing, log error and return
    if "lead_managers" not in data or not data["lead_managers"]:
        logging.error("No lead managers found - this is a required field")
        return {}
    
    # Build the standardized output dictionary
    standardized = {
        "lead_managers": [],
        "co_managers": [],
        "municipal_advisors": [],
        "counsels": [],
        "os_file_path": data.get("os_file_path"),
        "unprocessed_deal_scrape": {
            "lead_managers": data.get("lead_managers", []),
            "co_managers": data.get("co_managers", []),
            "municipal_advisors": data.get("municipal_advisors", []),
            "counsels": data.get("counsels", []),
        },
    }
    
    # Standardize lead managers
    for manager in data["lead_managers"]:
        if manager:  # Only process non-empty manager names
            canonical = standardizer.get_canonical_name(manager)
            if canonical:
                standardized["lead_managers"].append(canonical)
            else:
                logging.warning(f"Unknown lead manager name: {manager}")
                standardized["lead_managers"].append(manager)
    
    # Standardize other fields (co_managers, municipal_advisors, and counsels)
    for field in ["co_managers", "municipal_advisors", "counsels"]:
        if field in data:
            for item in data[field]:
                if item:  # Only process non-empty values
                    canonical = standardizer.get_canonical_name(item)
                    if canonical:
                        standardized[field].append(canonical)
                    else:
                        logging.warning(f"Unknown {field.replace('_', ' ')} name: {item}")
                        standardized[field].append(item)
    
    return standardized

def scrape_deal_info(url, driver=None, standardizer=None, download_os=True):
    """
    Scrapes and standardizes deal information from a given URL.
    
    Args:
        url (str): The URL of the deal page to process
        driver (webdriver, optional): Selenium WebDriver instance to use
        standardizer (CompanyStandardizer, optional): Instance for name standardization
        download_os (bool): If True, downloads OS files. Defaults to True.
        
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
            """
            Gets either href links or text content from a section based on class name.
            
            Args:
                class_name (str): CSS class name to search for
                section_name (str): Name of section for logging purposes
                
            Returns:
                list: List of either href links or text content found
            """
            try:
                # First try to find the section
                section = driver.find_element(By.CLASS_NAME, class_name)
                
                # Try to find links first
                links = section.find_elements(By.TAG_NAME, "a")
                if links:
                    return [link.get_attribute("href") for link in links]
                    
                # If no links found, look for text content in nologo class
                try:
                    nologo = section.find_element(By.CLASS_NAME, "nologo")
                    # Return text content in a list to maintain consistent return type
                    return [nologo.text.strip()]
                except Exception:
                    # If no nologo class found, try getting text from logo div
                    logo_div = section.find_element(By.CLASS_NAME, "logo")
                    text = logo_div.text.strip()
                    if text:
                        # Split by newlines and clean up any bullet points
                        return [item.strip().replace("•", "").strip() 
                               for item in text.split("\n")
                               if item.strip()]
                    return []
                    
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

        # Only download OS if the flag is True
        if download_os:
            os_file_path = download_os(driver)
            if os_file_path:  # Only add the path if we successfully downloaded the OS
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
