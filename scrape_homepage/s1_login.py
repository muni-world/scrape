from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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


        email_input = driver.find_element(By.ID, "login-email")
        email_input.clear()
        email_input.send_keys(email)

        password_input = driver.find_element(By.ID, "login-password")
        password_input.clear()
        password_input.send_keys(password)

        continue_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        continue_button.click()

    except Exception as e:
        print(f"An error occurred: {e}")
