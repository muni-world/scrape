from selenium import webdriver
from dotenv import load_dotenv
import os

def load_credentials():
    """
    Loads email and password from .env file
    Returns:
        tuple: (email, password)
    """
    load_dotenv()
    return os.getenv("MUNIOS_EMAIL"), os.getenv("MUNIOS_PASSWORD")

def initialize_driver():
    """
    Initializes and returns a Chrome webdriver
    Returns:
        webdriver: Chrome driver instance
    """
    return webdriver.Chrome()