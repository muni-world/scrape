import logging

def setup_logging():
    """
    Basic logging setup for the project.
    Logs to both console and a file with simple formatting.
    """
    # Set up basic configuration
    logging.basicConfig(
        level=logging.INFO,  # Only show INFO level and above
        format="%(asctime)s - %(levelname)s - %(message)s",  # Simple format
        handlers=[
            logging.FileHandler("app.log"),  # Log to file
            logging.StreamHandler()  # Log to console
        ]
    )
    logging.info("Logging started")