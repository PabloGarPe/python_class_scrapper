import tempfile
from pathlib import Path
import shutil

from playwright.async_api import Page, Browser, BrowserContext, async_playwright

from typing import Optional
from contextlib import asynccontextmanager

class ScrapperManager:
    """Manager class to handle scrapping operations."""
    
    # Timeouts for Playwright
    PAGE_LOAD_TIMEOUT = 120000 # 2 minutes
    SELECTOR_TIMEOUT = 60000 # 1 minute
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.temp_dir: Optional[str] = None
        
    async def initialize(self):
        """Initialize the navigator with a temporary directory."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.temp_dir = tempfile.mkdtemp(prefix="xlsx_scrapping_")
        
        self.context = await self.browser.new_context(
            accept_downloads=True
        )
    
    async def create_page(self) -> Page:
        """Create a new page in the current browser context."""
        if self.context is None:
            raise Exception("Browser context is not initialized.")
        page = await self.context.new_page()
        page.set_default_navigation_timeout(self.PAGE_LOAD_TIMEOUT)
        page.set_default_timeout(self.SELECTOR_TIMEOUT)
        return page
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
    @asynccontextmanager
    async def get_page(self):
        """Context manager to get a page and ensure cleanup."""
        page = await self.create_page()
        try:
            yield page
        finally:
            await page.close()