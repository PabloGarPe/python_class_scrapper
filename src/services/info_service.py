from playwright.async_api import Page, Error as PlaywrightError
from ..utils.settings import INFO_SITE_URL

from ..utils.settings import get_logger

logger = get_logger()

class InfoService:
    """Service for scrapping the software information from web pages."""
    
    SELECTOR_TIMEOUT = 60000 # 1 minute
    MAX_RETRIES = 3
    
    def __init__(self, scrapper_manager):
        self.scrapper_manager = scrapper_manager
        self.site_url = INFO_SITE_URL
        
    async def scrape_and_process(self, uo_value: str):
        """Scrape information based on the provided 'uo' value and process it."""
        
        async with self.scrapper_manager.get_page() as page:
            page = await self.get_element_by_uo(page, uo_value)
            
            if page is None:
                return {
                    "success": False,
                    "uo": uo_value,
                    "classes": []
                }
            
            class_list = await self.getListClass(page)
            
            result = {
                "success": True,
                "uo": uo_value,
                "classes": class_list
            }
            return result
        
    async def get_element_by_uo(self, page: Page, uo_value: str) -> Page:
        """
        Retrieve a web element using a custom 'uo' attribute.
        """
        
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            logger.info(f"[Attempt {retry_count + 1}/{self.MAX_RETRIES}] Navigating to the site URL.")
            
            try:
                await page.goto(self.site_url, wait_until="load")
                logger.info("Page loaded successfully.")
            except PlaywrightError as e:
                logger.warning(f"Failed to load page (attempt {retry_count + 1})")
                raise
            
            element = page.locator(f'a:has-text("{uo_value}")').first
            try:
                href = await element.get_attribute("href")
                if href:
                    logger.info(f"Found element with href: {href}")
                    await page.goto(href, wait_until="load")
                    logger.info("Navigated to the element's href successfully.")
                    return page
                else:
                    logger.warning(f"No href found for the element with uo_value: {uo_value}")
            except PlaywrightError as e:
                logger.warning(f"Error retrieving href (attempt {retry_count + 1}): {e}")
                
            retry_count += 1
            logger.info("Retrying...")
            
        logger.error(f"Failed to retrieve element with uo_value: {uo_value} after {self.MAX_RETRIES} attempts.")
            
        return None
    
    async def getListClass(self, page: Page) -> list:
        """ Extract a list of class names from the page."""
        
        class_elements = page.locator('h1 + p')
        class_text = await class_elements.all_text_contents()
        class_list = class_text[0].split(": ")[1].split("; ")
        return class_list