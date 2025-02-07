from datetime import datetime
from zoneinfo import ZoneInfo
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import logging

# On windows pip install tzdata because time zone data is not installed by default. Enables use of ZoneInfo.

def scrape_deals(driver, sector):
    """
    Scrapes deal information from the Munios website table.
    
    Args:
        driver: Selenium WebDriver instance
        sector (str): Sector filter being used (e.g. 'HC')
    
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
                
                # Skip this row if it's an Investor Update
                if "Investor Update" in deal_method:
                    continue
                    
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

                
                # Try to find description (second span) with safer selector
                try:
                    # Use adjacent sibling selector to find span after <p> tag
                    description_span = deal_cell.find_element(By.CSS_SELECTOR, "td.td4 > p + span")
                    series_name_obligor = description_span.text
                except NoSuchElementException:
                    series_name_obligor = "N/A"  # Set default value if not found
                    # Consider logging a warning here if needed

                # Extract underwriters and advisors
                underwriters_advisors = row.find_element(By.CLASS_NAME, "td6").text.split("\n")
                
                # Extract date from the webpage.
                date_str = row.find_element(By.CLASS_NAME, "td7").find_element(By.TAG_NAME, "p").text

                try:
                    # Parse as naive datetime (no timezone info)
                    naive_date = datetime.strptime(date_str, "%m/%d/%y")
                    
                    # Create timezone-aware datetime in NYC time
                    ny_time = naive_date.replace(tzinfo=ZoneInfo("America/New_York"))
                    
                    # Convert to UTC
                    utc_date = ny_time.astimezone(ZoneInfo("UTC"))
                    
                    parsed_date = utc_date
                    logging.debug(f"Converted NYC time {naive_date} to UTC: {utc_date}")

                except Exception as parse_error:
                    logging.error("Error parsing date: %s (Original: %s)", parse_error, date_str)
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
                    "sector": sector,
                    "type": deal_type,
                    "method": deal_method,
                    "state": state,
                    "issuer": issuer,
                    "total_par": total_par,
                    "series_name_obligor": series_name_obligor,
                    "underwriters_advisors": underwriters_advisors,
                    "date": parsed_date,
                    "url": f"https://www.munios.com/{deal_url}",
                    "unprocessed_homepage_scrape": {
                        "total_par": total_par_str,
                        "date": date_str,
                    }
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
