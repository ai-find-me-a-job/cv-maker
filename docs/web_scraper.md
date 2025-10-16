# Web Scraper Documentation

## Overview

The `JobWebScraper` class provides simple web scraping capabilities for job vacancy pages using Playwright headless browser. It extracts the complete DOM HTML and text content after JavaScript execution, letting the LLM handle content extraction.

## Features

- **Headless Browser**: Uses Playwright's Chromium browser for JavaScript rendering
- **Simple Extraction**: Gets full HTML and text content after page load
- **JavaScript Support**: Waits for dynamic content to load
- **Error Handling**: Graceful handling of failed requests and timeouts
- **Async Support**: Fully asynchronous for better performance

## Installation

1. Install Playwright:
```bash
pip install playwright
```

2. Install browser binaries:
```bash
playwright install chromium
```

Or use the setup script:
```bash
python setup_playwright.py
```

## Usage

### Basic Usage

```python
from app.cv_maker.web_scraper import scrape_job_url

# Simple one-time scraping
result = await scrape_job_url("https://example.com/job-posting")

if result["status"] == "success":
    print(f"Page Title: {result['page_title']}")
    print(f"HTML Length: {len(result['html'])} characters")
    print(f"Text Content: {result['text'][:500]}...")  # First 500 chars
```

### Advanced Usage

```python
from app.cv_maker.web_scraper import JobWebScraper

# Using the scraper class for multiple URLs
async with JobWebScraper(headless=True) as scraper:
    for url in job_urls:
        result = await scraper.scrape_job_page(url)
        # Process result...
```

### Integration with Workflow

The scraper is integrated into the CV workflow:

```python
from app.cv_maker.workflow import CVWorkflow

workflow = CVWorkflow()
result = await workflow.run(job_url="https://example.com/job-posting")
```

## Supported Sites

### LinkedIn Jobs
- Extracts job title, company name, and full description
- Handles LinkedIn's specific HTML structure
- Works with both public and authenticated pages

### Indeed
- Extracts structured job information
- Handles Indeed's dynamic content loading
- Works with job detail pages

### Glassdoor
- Extracts job postings and company information
- Handles Glassdoor's specific selectors
- Works with job detail pages

### Generic Sites
- Falls back to general content extraction
- Uses common job posting patterns
- Extracts main content areas

## Configuration

### Browser Options

```python
scraper = JobWebScraper(
    headless=True,      # Run in headless mode
    timeout=30000       # 30 second timeout
)
```

### Custom Headers

The scraper automatically sets browser-like headers:
- User-Agent: Chrome 120 on Windows
- Accept headers for HTML content
- DNT (Do Not Track) enabled
- Connection keep-alive

## Return Format

```python
{
    "url": "https://example.com/job",
    "status": "success" | "error",
    "html": "Full HTML content of the page...",
    "text": "Plain text content of the page...",
    "page_title": "Page Title",
    "final_url": "https://final-url-after-redirects.com",
    "error": "Error message if status is error"
}
```

## Error Handling

The scraper handles various error scenarios:

- **Network timeouts**: Returns error status with timeout message
- **HTTP errors**: Captures and reports HTTP status codes
- **JavaScript failures**: Continues with available content
- **Selector failures**: Falls back to general extraction methods

## Testing

Run the test script to verify functionality:

```bash
python test_web_scraper.py
```

This will test:
- Browser initialization
- Basic scraping capabilities  
- Text extraction and cleaning
- Error handling

## Performance Tips

1. **Reuse Scraper Instance**: For multiple URLs, use the same scraper instance
2. **Headless Mode**: Always use headless=True for production
3. **Timeout Configuration**: Adjust timeout based on site responsiveness
4. **Content Limits**: Large pages are automatically truncated to avoid memory issues

## Troubleshooting

### Browser Installation Issues
```bash
# Reinstall browsers
playwright install chromium --force
```

### Memory Issues
```bash
# Increase timeout for slow sites
scraper = JobWebScraper(timeout=60000)  # 60 seconds
```

### Site-Specific Issues
Check the browser console for JavaScript errors:
```python
# Run with headless=False to see browser
scraper = JobWebScraper(headless=False)
```

## Security Considerations

- The scraper respects robots.txt when possible
- Rate limiting should be implemented for large-scale scraping
- Some sites may block automated access
- Always check site terms of service before scraping