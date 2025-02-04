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