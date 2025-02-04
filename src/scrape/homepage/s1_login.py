from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

def login(driver, email, password):
    """
    Logs into the Munios website using provided credentials.
    
    Args:
        driver: Selenium WebDriver instance
        email: String containing the user's email
        password: String containing the user's password
        
    Returns:
        None
    """
    try:
        # Wait for email input to be present (this ensures the page is loaded)
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-email"))
        )
        email_input.clear()
        email_input.send_keys(email)

        # Proceed with the rest of the elements without explicit waits
        password_input = driver.find_element(By.ID, "login-password")
        password_input.clear()
        password_input.send_keys(password)

        continue_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        continue_button.click()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
