import logging
from typing import Any, Dict, Optional

from playwright.async_api import Browser, async_playwright

from .exceptions import WebScrapError


class JobWebScraper:
    """
    Web scraper for job vacancy pages using Playwright headless browser.
    Handles JavaScript-heavy sites and anti-bot protection.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.logger = logging.getLogger(__name__)
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()

    async def start_browser(self) -> None:
        """Start the Playwright browser."""
        self.logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()

        # Use Chromium for better compatibility
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
            ],
        )
        self.logger.info("Browser started successfully")

    async def close_browser(self) -> None:
        """Close the Playwright browser."""
        if self.browser:
            await self.browser.close()
            self.logger.info("Browser closed")
        if hasattr(self, "playwright"):
            await self.playwright.stop()

    async def scrape_job_page(self, url: str) -> Dict[str, Any]:
        """
        Scrape a job vacancy page and extract DOM HTML.

        Args:
            url: Job vacancy URL to scrape

        Returns:
            Dictionary containing scraped HTML and metadata

        Raises:
            WebScrapError: If scraping fails
        """
        if not self.browser:
            await self.start_browser()

        self.logger.info(f"Scraping job page: {url}")
        if not self.browser:
            raise WebScrapError("Browser is not initialized")
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )

        page = await context.new_page()

        try:
            # Navigate to the page
            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=self.timeout
            )

            if not response or response.status >= 400:
                raise WebScrapError(
                    f"Failed to load page: HTTP {response.status if response else 'No response'}"
                )

            self.logger.info(f"Page loaded successfully (status: {response.status})")

            # Wait for JavaScript to execute
            await page.wait_for_timeout(3000)  # Wait 3 seconds for JS to execute

            # Extract the full HTML content
            html_content = await page.content()

            # Extract page text content
            page_text = await page.evaluate("() => document.body.innerText") or ""

            return {
                "url": url,
                "status": "success",
                "html": html_content,
                "text": page_text,
                "page_title": await page.title(),
                "final_url": page.url,  # In case of redirects
            }

        except Exception as e:
            raise WebScrapError(f"Error scraping job page {url}: {e}")

        finally:
            await context.close()


# Convenience function for one-time scraping
async def scrape_job_url(url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Convenience function to scrape a single job URL.

    Args:
        url: Job vacancy URL to scrape
        headless: Whether to run browser in headless mode

    Returns:
        Dictionary containing scraped content and metadata
    """
    async with JobWebScraper(headless=headless) as scraper:
        return await scraper.scrape_job_page(url)
