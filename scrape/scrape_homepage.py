from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os

# Load credentials from environment variables
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

# Initialize the Chrome driver
driver = webdriver.Chrome()

try:
    # Open the webpage
    driver.get("https://login.munios.com/")

    # Wait for the page to load
    time.sleep(2)  # Adjust the sleep time as necessary

    # Locate the email input field and enter the email
    email_input = driver.find_element(By.ID, "login-email")  # Replace with the actual ID or other locator
    email_input.clear()
    email_input.send_keys(email)  # Use email from environment variable

    # Locate the password input field and enter the password
    password_input = driver.find_element(By.ID, "password")  # Replace with the actual ID or other locator
    password_input.clear()
    password_input.send_keys(password)  # Use password from environment variable

    # Locate the continue button and click it
    continue_button = driver.find_element(By.ID, "continue")  # Replace with the actual ID or other locator
    continue_button.click()

    # Wait for the next page to load
    time.sleep(5)  # Adjust the sleep time as necessary

finally:
    # Close the browser
    driver.quit()
