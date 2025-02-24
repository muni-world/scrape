from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

def apply_filters(driver, sector):
    """
    Applies filters for Sector = Healthcare and Type: Finals Only, then clicks Show.

    Args:
        driver: Selenium WebDriver instance
        sector: Sector code to apply filters for

    Returns:
        None
    """
    try:
        # Wait for the filters to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".rowFilter"))
        )

        # Select Sector = Healthcare
        sector_dropdown = driver.find_element(By.ID, "txtAdvSector")
        sector_dropdown.click()
        healthcare_option = driver.find_element(By.CSS_SELECTOR, f"#txtAdvSector option[value='{sector}']")
        healthcare_option.click()

        # Select Timeframe = Past week (options: -7, -30, -365, ALL)
        timeframe_dropdown = driver.find_element(By.ID, "txtAdvTime")
        timeframe_dropdown.click()
        past_week_option = driver.find_element(By.CSS_SELECTOR, "#txtAdvTime option[value='ALL']")
        past_week_option.click()


        # Select Type: Finals Only
        finals_only_radio = driver.find_element(By.CSS_SELECTOR, "input#rbType3")
        finals_only_radio.click()

        # Click Show button
        show_button = driver.find_element(By.ID, "btnAdvance")
        show_button.click()

    except Exception as e:
        logging.error(f"An error occurred while applying filters: {e}")