from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore

def load_muni_credentials():
    """
    Loads email and password from .env file
    
    Returns:
        tuple: (email, password)
    """
    load_dotenv()
    return os.getenv("MUNIOS_EMAIL"), os.getenv("MUNIOS_PASSWORD")

def initialize_firestore():
    """
    Initializes and returns a Firestore client.
    If Firebase app is already initialized, returns a new client.
    Otherwise, initializes the app with credentials first.
    
    Returns:
        firestore.Client: Initialized Firestore client
    """
    try:
        firebase_admin.get_app()  # Try retrieving an existing Firebase app
    except ValueError:
        # If no app is found, initialize using service account key file
        cred = credentials.Certificate("secrets/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    
    return firestore.client()