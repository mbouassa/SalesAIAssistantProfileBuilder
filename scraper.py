"""
Website Scraper Module
Uses Playwright to crawl websites and extract all visible text from pages.
"""

import asyncio
from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse


class WebsiteScraper:
    """Scrapes a website and extracts text content from all discoverable pages."""
    
    def __init__(self, start_url: str, max_pages: int = 10):
        self.start_url = start_url
        self.max_pages = max_pages
        self.base_domain = urlparse(start_url).netloc
        self.visited_urls: set = set()
        self.pages_data: List[Dict] = []
    
    async def scrape(self) -> Dict:
        """Main entry point - scrapes the website and returns structured data."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Start with the main URL
                await self._scrape_page(page, self.start_url)
                
                # Find and click through navigation items
                await self._discover_pages(page, browser)
                
            except Exception as e:
                print(f"⚠️  Error during scraping: {e}")
            finally:
                await browser.close()
        
        return {
            "home_url": self.start_url,
            "pages": self.pages_data
        }
    
    async def _scrape_page(self, page: Page, url: str) -> Optional[Dict]:
        """Scrape a single page and extract all visible text."""
        if url in self.visited_urls:
            return None
        
        if len(self.visited_urls) >= self.max_pages:
            return None
        
        # Only scrape pages from the same domain
        if urlparse(url).netloc != self.base_domain:
            return None
        
        self.visited_urls.add(url)
        
        try:
            print(f"  📄 Scraping: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)  # Extra wait for dynamic content
            
            # Extract page title
            title = await page.title()
            
            # Extract all visible text
            text = await page.evaluate('''() => {
                // Get all visible text from the page
                return document.body.innerText;
            }''')
            
            # Extract clickable elements (buttons, links) with their text
            clickables = await page.evaluate('''() => {
                const elements = [];
                
                // Buttons
                document.querySelectorAll('button').forEach(el => {
                    const text = el.innerText.trim();
                    if (text && text.length < 100) {
                        elements.push({type: 'button', text: text});
                    }
                });
                
                // Links
                document.querySelectorAll('a').forEach(el => {
                    const text = el.innerText.trim();
                    const href = el.href;
                    if (text && text.length < 100) {
                        elements.push({type: 'link', text: text, href: href});
                    }
                });
                
                // Clickable divs/spans with role="button"
                document.querySelectorAll('[role="button"]').forEach(el => {
                    const text = el.innerText.trim();
                    if (text && text.length < 100) {
                        elements.push({type: 'button', text: text});
                    }
                });
                
                return elements;
            }''')
            
            # Extract navigation items
            nav_items = await page.evaluate('''() => {
                const items = [];
                
                // Look for nav elements
                document.querySelectorAll('nav a, [role="navigation"] a, header a').forEach(el => {
                    const text = el.innerText.trim();
                    const href = el.href;
                    if (text && text.length < 50 && href) {
                        items.push({text: text, href: href});
                    }
                });
                
                // Also look for tab-like elements
                document.querySelectorAll('[role="tab"], [role="tablist"] button').forEach(el => {
                    const text = el.innerText.trim();
                    if (text && text.length < 50) {
                        items.push({text: text, href: null, isTab: true});
                    }
                });
                
                return items;
            }''')
            
            page_data = {
                "url": url,
                "title": title,
                "text": text[:15000] if text else "",  # Limit text length
                "clickables": clickables[:50],  # Limit number of clickables
                "nav_items": nav_items[:20]
            }
            
            self.pages_data.append(page_data)
            return page_data
            
        except Exception as e:
            print(f"  ⚠️  Failed to scrape {url}: {e}")
            return None
    
    async def _discover_pages(self, page: Page, browser: Browser):
        """Discover and scrape additional pages through navigation."""
        if not self.pages_data:
            return
        
        # Collect unique navigation URLs from the first page
        first_page = self.pages_data[0]
        nav_urls = set()
        
        for item in first_page.get('nav_items', []):
            href = item.get('href')
            if href and urlparse(href).netloc == self.base_domain:
                nav_urls.add(href)
        
        # Also check clickable links
        for item in first_page.get('clickables', []):
            if item.get('type') == 'link':
                href = item.get('href')
                if href and urlparse(href).netloc == self.base_domain:
                    nav_urls.add(href)
        
        # Scrape each discovered URL
        for url in list(nav_urls)[:self.max_pages - 1]:
            if url not in self.visited_urls:
                await self._scrape_page(page, url)
        
        # Also try clicking tabs if present
        await self._click_tabs(page)
    
    async def _click_tabs(self, page: Page):
        """Click through tab elements to discover more content."""
        try:
            # Go back to start URL
            await page.goto(self.start_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1)
            
            # Find tab elements
            tabs = await page.query_selector_all('[role="tab"], [data-tab], .tab')
            
            for i, tab in enumerate(tabs[:5]):  # Limit to 5 tabs
                try:
                    tab_text = await tab.inner_text()
                    if not tab_text.strip():
                        continue
                    
                    # Click the tab
                    await tab.click()
                    await asyncio.sleep(1)
                    
                    # Get current URL (might have changed)
                    current_url = page.url
                    
                    # Check if this is new content
                    if current_url not in self.visited_urls or True:  # Always capture tab content
                        text = await page.evaluate('() => document.body.innerText')
                        title = await page.title()
                        
                        # Check if content is significantly different
                        tab_data = {
                            "url": current_url,
                            "title": f"{title} - {tab_text.strip()}",
                            "text": text[:15000] if text else "",
                            "is_tab": True,
                            "tab_name": tab_text.strip()
                        }
                        
                        # Only add if content seems different
                        if not any(p.get('text', '')[:500] == text[:500] for p in self.pages_data):
                            self.pages_data.append(tab_data)
                            print(f"  📑 Found tab: {tab_text.strip()}")
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass  # Tabs are optional, don't fail on errors


async def scrape_website(url: str, max_pages: int = 10) -> Dict:
    """Convenience function to scrape a website."""
    scraper = WebsiteScraper(url, max_pages)
    return await scraper.scrape()


# For testing
if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    result = asyncio.run(scrape_website(url))
    print(f"\n✅ Scraped {len(result['pages'])} pages")
    for page in result['pages']:
        print(f"  - {page['title']}: {len(page.get('text', ''))} chars")

