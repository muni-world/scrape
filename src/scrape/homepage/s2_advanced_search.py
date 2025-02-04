from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def click_advanced_search(driver):
    """
    Clicks the 'Advanced Search' button on the Munios website.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        None
    """
    try:
        # Wait for the Advanced Search button to be clickable
        advanced_search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "advSearch"))
        )
        
        # Click the Advanced Search button
        advanced_search_button.click()
        
    except Exception as e:
        print(f"An error occurred while clicking Advanced Search: {e}")
