from playwright.async_api import Page, Error as PlaywrightError
from ..utils.settings import INFO_SITE_URLS

from ..utils.settings import get_logger

logger = get_logger()

class InfoService:
    """Service for scrapping the software information from web pages."""
    
    SELECTOR_TIMEOUT = 60000 # 1 minute
    MAX_RETRIES = 3
    
    def __init__(self, scrapper_manager):
        self.scrapper_manager = scrapper_manager
        self.site_urls = INFO_SITE_URLS
        
    async def scrape_and_process(self, uo_value: str):
        """Scrape information based on the provided 'uo' value and process it."""
        
        all_classes = []
        success_count = 0
        
        for url_index, site_url in enumerate(self.site_urls):
            logger.info(f"Scraping from URL {url_index + 1}/{len(self.site_urls)}: {site_url}")
            
            async with self.scrapper_manager.get_page() as page:
                try:
                    result_page = await self.get_element_by_uo_single(page, uo_value, site_url)
                    
                    if result_page is not None:
                        class_list = await self.getListClass(result_page)
                        all_classes.extend(class_list)
                        success_count += 1
                        logger.info(f"Successfully scraped {len(class_list)} classes from URL {url_index + 1}")
                    else:
                        logger.warning(f"No data found for {uo_value} in URL {url_index + 1}")
                        
                except Exception as e:
                    logger.error(f"Error scraping URL {url_index + 1}: {e}")
                    continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_classes = []
        for cls in all_classes:
            if cls not in seen:
                seen.add(cls)
                unique_classes.append(cls)
        
        return {
            "success": success_count > 0,
            "uo": uo_value,
            "classes": unique_classes,
            "sources_found": success_count
        }
        
    async def get_element_by_uo_single(self, page: Page, uo_value: str, site_url: str) -> Page | None:
        """
        Retrieve a web element using a custom 'uo' attribute from a single URL.
        """
        
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            logger.info(f"[Attempt {retry_count + 1}/{self.MAX_RETRIES}] Navigating to {site_url}")
            
            try:
                await page.goto(site_url, wait_until="load")
                logger.info("Page loaded successfully.")
            except PlaywrightError as e:
                logger.warning(f"Failed to load page (attempt {retry_count + 1}): {e}")
                retry_count += 1
                continue
            
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
            if retry_count < self.MAX_RETRIES:
                await page.wait_for_timeout(1000)  # Wait 1 second before retry
        
        logger.warning(f"Failed to retrieve element with uo_value: {uo_value} from {site_url}")
        return None
    
    async def get_element_by_uo(self, page: Page, uo_value: str) -> Page:
        """
        Retrieve a web element using a custom 'uo' attribute.
        Tries all configured URLs until one works.
        
        This method is kept for backward compatibility but now tries all URLs.
        """
        
        # Try each URL from the configuration
        for url_index, site_url in enumerate(self.site_urls):
            logger.info(f"Trying URL {url_index + 1}/{len(self.site_urls)}: {site_url}")
            
            result = await self.get_element_by_uo_single(page, uo_value, site_url)
            if result is not None:
                return result
            
            logger.warning(f"Failed with URL {site_url}, trying next URL if available...")
            
        logger.error(f"Failed to retrieve element with uo_value: {uo_value} after trying all URLs.")
        return None
    
    async def getListClass(self, page: Page) -> list:
        """ Extract a list of class names from the page."""
        
        class_elements = page.locator('h1 + p')
        class_text = await class_elements.all_text_contents()
        class_list = class_text[0].split(": ")[1].split("; ")
        return class_list