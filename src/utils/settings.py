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
info_site_url_raw = os.getenv("INFO_SITE_URL", "https://gobierno.ingenieriainformatica.uniovi.es/grado/gd/?y=25-26&t=s2")
INFO_SITE_URLS = [url.strip() for url in info_site_url_raw.split(',')]
MATH_SITE_URL = os.getenv("MATH_SITE_URL", "https://unioviado-my.sharepoint.com/:f:/g/personal/perezfernandez_uniovi_es/Eu9qlYNQEYhMi2gDAxmrmvABPSoVDkYi4cCTXf_ZVyql9w?e=a3ZGBs")
