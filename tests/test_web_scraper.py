"""
Tests for the web scraper component.
"""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio

from src.core.web_scraper import scrape_job_url


class TestWebScraper:
    """Test the web scraping functionality."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.title = AsyncMock(return_value="Software Engineer Job | TechCorp")
        page.url = "https://example.com/job/123"
        page.content = AsyncMock(
            return_value="<html><body><h1>Job Title</h1><p>Job description content</p></body></html>"
        )
        page.locator.return_value.text_content = AsyncMock(
            return_value="Job description content"
        )
        return page

    @pytest.fixture
    def mock_browser(self, mock_page):
        """Create a mock Playwright browser."""
        browser = AsyncMock()
        context = AsyncMock()
        context.new_page.return_value = mock_page
        browser.new_context.return_value = context
        return browser

    @pytest.fixture
    def mock_playwright(self, mock_browser):
        """Create a mock Playwright instance."""
        playwright = AsyncMock()
        playwright.chromium.launch.return_value = mock_browser
        return playwright

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_success(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test successful job URL scraping."""
        # Setup mocks
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

        job_url = "https://example.com/job/123"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result
        assert result["status"] == "success"
        assert result["text"] == "Job description content"
        assert result["page_title"] == "Software Engineer Job | TechCorp"
        assert result["final_url"] == "https://example.com/job/123"
        assert "error" not in result

        # Verify the interactions
        mock_playwright.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()
        mock_page.goto.assert_called_once_with(
            job_url, wait_until="networkidle", timeout=30000
        )

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_timeout(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test job URL scraping with timeout."""
        # Setup mocks to simulate timeout
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_page.goto.side_effect = asyncio.TimeoutError("Navigation timeout")

        job_url = "https://example.com/job/slow"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result indicates error
        assert result["status"] == "error"
        assert result["text"] == ""
        assert result["page_title"] == ""
        assert result["final_url"] == job_url
        assert "timeout" in result["error"].lower()

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_network_error(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test job URL scraping with network error."""
        # Setup mocks to simulate network error
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_page.goto.side_effect = Exception(
            "Network error: DNS_PROBE_FINISHED_NXDOMAIN"
        )

        job_url = "https://nonexistent-domain.com/job/123"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result indicates error
        assert result["status"] == "error"
        assert result["text"] == ""
        assert result["page_title"] == ""
        assert result["final_url"] == job_url
        assert "Network error" in result["error"]

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_invalid_url(self, mock_async_playwright):
        """Test job URL scraping with invalid URL."""
        job_url = "not-a-valid-url"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result indicates error
        assert result["status"] == "error"
        assert result["text"] == ""
        assert result["page_title"] == ""
        assert result["final_url"] == job_url
        assert "error" in result

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_empty_content(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test job URL scraping with empty page content."""
        # Setup mocks with empty content
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_page.title.return_value = "Empty Page"
        mock_page.locator.return_value.text_content.return_value = ""

        job_url = "https://example.com/empty-job"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result
        assert result["status"] == "success"  # Still success, just empty content
        assert result["text"] == ""
        assert result["page_title"] == "Empty Page"
        assert (
            result["final_url"] == "https://example.com/job/123"
        )  # from mock_page.url

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_with_redirects(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test job URL scraping with redirects."""
        # Setup mocks to simulate redirect
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_page.url = (
            "https://redirected-example.com/job/456"  # Different from original URL
        )

        job_url = "https://example.com/redirect-to-job"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result shows final URL after redirect
        assert result["status"] == "success"
        assert result["final_url"] == "https://redirected-example.com/job/456"

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_browser_launch_failure(
        self, mock_async_playwright, mock_playwright
    ):
        """Test job URL scraping when browser fails to launch."""
        # Setup mocks to simulate browser launch failure
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_playwright.chromium.launch.side_effect = Exception(
            "Failed to launch browser"
        )

        job_url = "https://example.com/job/123"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result indicates error
        assert result["status"] == "error"
        assert result["text"] == ""
        assert result["page_title"] == ""
        assert result["final_url"] == job_url
        assert "Failed to launch browser" in result["error"]

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_page_creation_failure(
        self, mock_async_playwright, mock_playwright, mock_browser
    ):
        """Test job URL scraping when page creation fails."""
        # Setup mocks to simulate page creation failure
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        context = AsyncMock()
        context.new_page.side_effect = Exception("Failed to create page")
        mock_browser.new_context.return_value = context

        job_url = "https://example.com/job/123"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result indicates error
        assert result["status"] == "error"
        assert result["text"] == ""
        assert result["page_title"] == ""
        assert result["final_url"] == job_url
        assert "Failed to create page" in result["error"]

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_content_extraction_strategies(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test different content extraction strategies."""
        # Setup mocks
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

        # Mock different selectors returning different content
        def mock_locator(selector):
            locator_mock = AsyncMock()
            if "body" in selector:
                locator_mock.text_content.return_value = (
                    "Full body content with job description"
                )
            elif "main" in selector:
                locator_mock.text_content.return_value = "Main content area"
            elif ".job-description" in selector:
                locator_mock.text_content.return_value = (
                    "Specific job description content"
                )
            else:
                locator_mock.text_content.return_value = ""
            return locator_mock

        mock_page.locator.side_effect = mock_locator

        job_url = "https://example.com/job/123"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify that content was extracted
        assert result["status"] == "success"
        assert len(result["text"]) > 0

        # Verify that multiple selectors were tried
        assert mock_page.locator.call_count >= 1

    @patch("src.core.web_scraper.async_playwright")
    async def test_scrape_job_url_special_characters_in_content(
        self, mock_async_playwright, mock_playwright, mock_browser, mock_page
    ):
        """Test job URL scraping with special characters in content."""
        # Setup mocks with special characters
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
        mock_page.title.return_value = "Job at R&D Corp - 100% Remote"
        mock_page.locator.return_value.text_content.return_value = "Job requires 5+ years experience with C++ & Python. Salary: $80,000-$120,000."

        job_url = "https://example.com/job/special-chars"

        # Call the function
        result = await scrape_job_url(job_url)

        # Verify the result preserves special characters
        assert result["status"] == "success"
        assert "R&D Corp" in result["page_title"]
        assert "100%" in result["page_title"]
        assert "C++" in result["text"]
        assert "$80,000-$120,000" in result["text"]
