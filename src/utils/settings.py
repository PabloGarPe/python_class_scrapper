import logging
from logging import getLogger

# Configure logger for the application
logger = getLogger(__name__)
logger.setLevel("DEBUG")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_logger():
    return logger