from typing import Any, Dict
from pathlib import Path

from playwright.async_api import Error as PlaywrightError, Page

from ..utils.settings import get_logger

logger = get_logger()

class MathService:
    """Service for scrapping math-related documents from a SharePoint site."""
    
    SELECTOR_TIMEOUT = 60000 # 1 minute
    MAX_RETRIES = 3 
    
    def __init__(self, scrapper_manager):
        self.scrapper_manager = scrapper_manager
        self.site_url = "https://unioviedo-my.sharepoint.com/:f:/g/personal/perezfernandez_uniovi_es/Eu9qlYNQEYhMi2gDAxmrmvABPSoVDkYi4cCTXf_ZVyql9w?e=a3ZGBs"
        
    async def scrape_and_process(self, uo_value: str) -> Dict[str, Any]:
        """Downloads and processes math schedules for a given UO value."""
        
        async with self.scrapper_manager.get_page() as page:
            file_path = await self._search_and_download_file(page, uo_value)
            
            if not file_path:
                return {
                    "success": False,
                    "uo": uo_value,
                    "classes": [],
                }
            
            result = self.process_xlsx_file(file_path)
            
            file_path.unlink(missing_ok=True) 
            
            return result
        
    async def _search_and_download_file(self, page, uo_value: str) -> str:
        """Searches for the file corresponding to the UO value and downloads it."""
        
        retry_count = 0
        while retry_count < self.MAX_RETRIES:
            try:
                logger.info(f"[Attempt {retry_count + 1}/{self.MAX_RETRIES}] Connecting to SharePoint for user {uo_value}")
            
                # Open sharepoint
                try:
                    await page.goto(self.site_url, wait_until="load")
                    logger.info("SharePoint page loaded.")
                except PlaywrightError:
                    logger.warning(f"Failed to load SharePoint (attempt {retry_count + 1})")
                    raise
                
                # Wait for rows to load
                try:
                    await page.wait_for_selector("[role='row']", timeout=self.SELECTOR_TIMEOUT)
                    logger.info("SharePoint loaded successfully.")
                except PlaywrightError:
                    logger.warning(f"Rows did not load in time (attempt {retry_count + 1})")
                    raise
                    
                # Search for scroll container
                scroll_container = await page.query_selector("div[class^='list_']")
                if not scroll_container:
                    logger.warning("Scroll container not found, using alternative method")
                    scroll_container = await page.query_selector("body")
                    
                    if not scroll_container:
                        raise Exception("No scroll container available")
                    
                # Search for the file with the UO value
                uo_value = uo_value.upper()
                target_filename = f"Lista_clases_{uo_value}@uniovi.es.xls"
                logger.info(f"Searching for file: {target_filename}")
                
                file_path = await self._scroll_and_find_file(
                    page, scroll_container, uo_value, target_filename
                )
                
                if file_path:
                    logger.info(f"File found and downloaded: {file_path}")
                    return file_path
                else:
                    logger.warning(f"File not found for UO {uo_value} (attempt {retry_count + 1})")
                    return None
                
            except Exception as e:
                logger.error(f"Error in attempt {retry_count + 1}: {e}")
                retry_count += 1
                
                if retry_count < self.MAX_RETRIES:
                    wait_time = 5 * retry_count
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    await page.wait_for_timeout(wait_time * 1000)
                else:
                    logger.error(f"Max retries reached for user {uo_value}")
                    return None
        
        return None
    
    
    async def _scroll_and_find_file(
        self, 
        page: Page,
        scroll_container,
        uo_value: str,
        target_filename: str
    ) -> Path | None:
        """Scrolls through the file list to find and download the target file."""
        
        scroll_attempts = 0
        max_scroll_attempts = 500
        
        while scroll_attempts < max_scroll_attempts:
            visible_rows = await scroll_container.query_selector_all("[role='row']")
            
            for row in visible_rows:
                try:
                    row_text = await row.inner_text()
                    
                    lines = row_text.split("\n")
                    if not lines:
                        continue
                    
                    file_name = lines[0].strip()
                    
                    if not file_name.startswith("Lista_clases_"):
                        continue
                    
                    if ".xls" in file_name:
                        xls_index = file_name.find(".xls") + 4
                        file_name = file_name[:xls_index]
                                        
                    logger.debug(f"Checking file: {file_name}")
                    
                    if file_name == target_filename:
                        logger.info(f"  Found target file: {file_name}")
                        
                        file_path = await self._download_file(page, row, file_name)

                        if file_path:
                            return file_path
                        else:
                            logger.warning(f"Failed to download {file_name}, continuing search...")
                            return None
                        
                except Exception as e:
                    logger.error(f"Error processing row: {e}")
                    continue
                
            # Scroll down
            try:
                await scroll_container.evaluate("el => el.scrollBy(0, 150)")
                await page.wait_for_timeout(300)
                scroll_attempts += 1
                
                if scroll_attempts % 50 == 0:
                    logger.info(f"Scrolled {scroll_attempts} times, still searching...")

            except Exception as e:
                logger.error(f"Error during scrolling: {e}")
                break
            
        logger.warning(f"Reached max scroll attempts ({max_scroll_attempts}) without finding the file.")
        return None
    
    async def _download_file(self, page: Page, row, file_name: str) -> Path | None:
        """Downloads the file from the given row element."""
        
        try:
            await row.click(button="right")
            await page.wait_for_timeout(500)
            
            try:
                async with page.expect_download(timeout=self.SELECTOR_TIMEOUT) as download_info:
                    await page.click("text=Descargar", timeout=10000)
            except PlaywrightError as e:
                logger.error(f"Timeout downloading file {file_name}: {e}")
                return None
            
            download = await download_info.value
            
            temp_dir = Path(self.scrapper_manager.temp_dir)
            safe_filename = file_name.replace(" ", "_").replace("/", "_")
            file_path = temp_dir / safe_filename
            
            await download.save_as(str(file_path))
            logger.info(f"Downloaded file to {file_path}")
            
            return file_path
        
        except Exception as e:
            logger.error(f"Error downloading file {file_name}: {e}")
            return None
        
    def process_xlsx_file(self, file_path: Path) -> Dict[str, Any]:
        """Processes the downloaded XLSX file and extracts class information."""
        
        # Placeholder for actual XLSX processing logic
        # This should read the XLSX file and extract relevant data
        
        # For demonstration, returning a dummy result
        return {
            "success": True,
            "uo": file_path.stem.split("_")[-1],
            "classes": ["Class1", "Class2", "Class3"],
        }