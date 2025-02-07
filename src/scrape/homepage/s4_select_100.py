from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

def select_100_deals(driver):
    """
    Handles the pagination selection on the Munios website by selecting the '100' option.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        None
    """
    try:
        # Wait for the pagination list to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "fltPage"))
        )

        # Use JavaScript to click the element since it doesn't have a click handler
        hundred_option = driver.find_element(By.XPATH, "//ul[@id='fltPage']/li[text()='10']")
        driver.execute_script("arguments[0].click();", hundred_option)

    except Exception as e:
        logging.error(f"An error occurred while filtering results: {e}")