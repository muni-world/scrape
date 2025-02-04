from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
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
                
                # Extract amount (if present)
                amount = ""
                try:
                    amount_text = deal_cell.find_element(By.TAG_NAME, "p").text
                    amount = amount_text.split("$")[-1].strip("()")
                except:
                    pass
                
                # Extract description
                description = deal_cell.find_element(By.TAG_NAME, "span").text
                
                # Extract underwriters and advisors
                underwriters_advisors = row.find_element(By.CLASS_NAME, "td6").text.split("\n")
                
                # Extract date
                date = row.find_element(By.CLASS_NAME, "td7").find_element(By.TAG_NAME, "p").text
                
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
                    "amount": amount,
                    "description": description,
                    "underwriters_advisors": underwriters_advisors,
                    "date": date,
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
