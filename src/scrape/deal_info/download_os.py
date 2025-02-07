from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
import time

def setup_download(driver):
    """
    Configures the browser to automatically download files to the specified directory.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        None
    """
    try:
        if driver.capabilities['browserName'].lower() == 'chrome':
            # Calculate default path instead of querying Chrome
            # works on windows
            default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            params = {
                "behavior": "allow",
                "downloadPath": default_downloads
            }
            driver.execute_cdp_cmd("Page.setDownloadBehavior", params)
        else:
            raise NotImplementedError("Automatic downloads currently only supported for Chrome")
    except Exception as e:
        logging.warning(f"CDP command warning: {str(e)}")
        logging.info("Downloads will use browser's default behavior")

def download_os(driver):
    """
    Handles the complete OS (Official Statement) download process including:
    1. Setting up download configuration
    2. Clicking the download button
    3. Agreeing to terms
    4. Downloading the file
    5. Returning the full path to the downloaded file
    

    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        str: The full path to the downloaded file
    """
    try:

        # Configure download settings
        setup_download(driver)
        
        # Wait for the download section to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.download"))
        )
        
        # Get the file name from the file div
        file_info = driver.find_element(By.CSS_SELECTOR, "div.file").text
        file_name = file_info.split("(")[0].strip()  # Remove the size information
        
        # Wait for the download button to be clickable
        download_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-danger.btn-lg"))
        )
        
        # Click the download button
        download_button.click()
        logging.info(f"Initiated download for file: {file_name}")
        
        # Wait for and click the agree button
        agree_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-danger.btn-lg[onclick*='sendFile']"))
        )
        agree_button.click()
        logging.info("Agreed to terms and conditions")
        
        # Construct full file path
        download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        full_file_path = os.path.join(download_path, file_name)
        
        # Wait for download completion
        if not wait_for_download_complete(download_path, file_name, timeout=60):
            raise Exception(f"Download failed - file '{file_name}' not found after waiting")

        logging.info(f"Successfully downloaded: {full_file_path}")
        return full_file_path
        
    except Exception as e:
        logging.error(f"Error during OS download process: {e}")
        raise

def wait_for_download_complete(download_path, filename, timeout=30):
    """
    Waits for a file to finish downloading by monitoring temporary files.
    
    Args:
        download_path: Path to download directory
        filename: Expected filename (without .tmp extension)
        timeout: Maximum wait time in seconds
        
    Returns:
        bool: True if download completed successfully
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        # Check for both temp files and final file
        temp_files = [f for f in os.listdir(download_path) if f.endswith(".tmp")]
        final_file = os.path.join(download_path, filename)
        
        if os.path.exists(final_file) and not temp_files:
            return True
        time.sleep(1)
    
    return False


    
