import logging
from logging import getLogger

# Configure logger for the application
logger = getLogger(__name__)
logger.setLevel("INFO")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_logger():
    return logger

# Load the variables from a .env file
from dotenv import load_dotenv
import os

load_dotenv()

# Application settings
INFO_SITE_URL = os.getenv("INFO_SITE_URL", "https://gobierno.ingenieriainformatica.uniovi.es/grado/gd/?y=25-26&t=s2")
MATH_SITE_URL = os.getenv("MATH_SITE_URL", "https://unioviedo-my.sharepoint.com/:f:/g/personal/perezfernandez_uniovi_es/Eu9qlYNQEYhMi2gDAxmrmvABPSoVDkYi4cCTXf_ZVyql9w?e=a3ZGBs")
