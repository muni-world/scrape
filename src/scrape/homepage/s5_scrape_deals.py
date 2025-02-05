import datetime  # Import datetime module to work with dates
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging


def scrape_deals(driver):
    """
    Scrapes deal information from the Munios website table.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        list: List of dictionaries containing deal information
    """
    try:
        # Don't use WebDriverWait because it's not reliable.
        sleep(3)

        # Get all deal rows
        deals = []
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody.dealList tr")
        
        for row in rows:
            try:
                # Extract deal type and method
                type_box = row.find_element(By.CLASS_NAME, "typeBox")
                deal_type = type_box.find_element(By.CLASS_NAME, "l1").text
                deal_method = type_box.find_element(By.CLASS_NAME, "l2").text
                
                # Extract state code
                state = row.find_element(By.CLASS_NAME, "td3").text
                
                # Extract deal details
                deal_cell = row.find_element(By.CLASS_NAME, "td4")
                issuer = deal_cell.find_element(By.CLASS_NAME, "issuer").text
                
                # Initialize total_par_text to ensure it's defined.
                total_par_text = ""
                try:
                    # Get the text that likely contains a dollar amount (e.g., "$1,234.56")
                    total_par_text = deal_cell.find_element(By.TAG_NAME, "p").text
                    # Clean the text by splitting at "$", stripping any parentheses, and removing commas.
                    total_par_str = total_par_text.split("$")[-1].strip("()").replace(",", "")
                    # Convert the cleaned string into a floating point number.
                    total_par = float(total_par_str)
                except Exception as exc:
                    # Log errors that occur during amount parsing.
                    logging.error("Error parsing amount: %s", exc)
                    total_par = None

                
                # Extract description
                description = deal_cell.find_element(By.TAG_NAME, "span").text
                
                # Extract underwriters and advisors
                underwriters_advisors = row.find_element(By.CLASS_NAME, "td6").text.split("\n")
                
                # Extract date from the webpage.
                date_str = row.find_element(By.CLASS_NAME, "td7").find_element(By.TAG_NAME, "p").text

                try:
                    # Parse the raw date string directly.
                    # For example, "01/30/25" becomes a datetime representing 2025-01-30 00:00:00.
                    parsed_date = datetime.datetime.strptime(date_str, "%m/%d/%y")

                except Exception as parse_error:
                    # Log the error if the conversion fails and set parsed_date to None.
                    logging.error("Error parsing date: %s", parse_error)
                    parsed_date = None
                
                # Extract deal URL

                onclick_attr = row.get_attribute("onclick")
                deal_url = ""
                if "window.location.assign" in onclick_attr:
                    # Extract URL from onclick attribute
                    deal_url = onclick_attr.split('window.location.assign("')[1].split('")')[0]
                elif "MyPopUpWin" in onclick_attr:
                    # Extract URL from popup window function
                    deal_url = onclick_attr.split('MyPopUpWin("')[1].split('"')[0]
                
                # Create deal dictionary
                deal = {
                    "type": deal_type,
                    "method": deal_method,
                    "state": state,
                    "issuer": issuer,
                    "total_par_dirty": total_par_text,
                    "total_par": total_par,
                    "description": description,
                    "underwriters_advisors": underwriters_advisors,
                    "date_dirty": date_str,
                    "date": parsed_date,
                    "url": f"https://www.munios.com/{deal_url}",

                }
                logging.info(f"Scraped hompage deal: {deal}")
                deals.append(deal)
                
            except Exception as e:
                logging.error(f"Error processing row: {e}")
                continue
        
        logging.info(f"Successfully scraped homepage and found {len(deals)} deals")
        return deals
        

    except Exception as e:
        logging.error(f"An error occurred while scraping deals: {e}")
        return []
