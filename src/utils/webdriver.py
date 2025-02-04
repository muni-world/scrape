from selenium import webdriver

def initialize_driver():
    """
    Initializes and returns a Chrome webdriver with common options.
    
    Returns:
        webdriver: Chrome driver instance
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(options=options)