#!/usr/bin/env python3
import os
import json
import argparse
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web_scraper')

class WebScraper:
    def __init__(self, headless=True):
        """Initialize web scraper for extracting reference content"""
        logger.info("Initializing web scraper")
        self.options = Options()
        
        # Only run headless if specified
        if headless:
            self.options.add_argument("--headless=new")  # Using new headless mode
        
        # Add necessary options for stability
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        self.driver = None
        
    def start(self):
        """Start the WebDriver"""
        try:
            chrome_driver_path = "./chromedriver-linux64/chromedriver"
            if not os.path.exists(chrome_driver_path):
                chrome_driver_path = "./chromedriver-linux64-new/chromedriver"
            
            if not os.path.exists(chrome_driver_path):
                logger.error("ChromeDriver not found in expected locations")
                return False
                
            service = Service(executable_path=chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=self.options)
            
            logger.info("WebDriver started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting WebDriver: {e}")
            return False
    
    def stop(self):
        """Stop the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping WebDriver: {e}")
    
    def search_for_references(self, subject, max_results=10, timeout=30):
        """Search for reference material based on the subject"""
        references = []
        
        if not self.driver:
            logger.error("WebDriver is not initialized, cannot perform search")
            return references
        
        try:
            logger.info(f"Searching for references on subject: {subject}")
            
            # Use Wikipedia for reliable content
            search_url = f"https://en.wikipedia.org/wiki/Special:Search?search={subject}&go=Go"
            logger.info(f"Accessing: {search_url}")
            
            self.driver.get(search_url)
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, "content"))
            )
            
            # Check if redirected to an article
            if "Special:Search" not in self.driver.current_url:
                logger.info("Direct article match found")
                article_url = self.driver.current_url
                article_title = self.driver.title.replace(" - Wikipedia", "")
                article_content = self._extract_article_content()
                
                if article_content and len(article_content) > 100:
                    references.append({
                        "url": article_url,
                        "title": article_title,
                        "content": article_content
                    })
                    logger.info(f"Extracted content from {article_title}")
            else:
                # Process search results
                logger.info("Processing search results")
                search_results = self.driver.find_elements(By.CSS_SELECTOR, ".mw-search-result")
                
                count = 0
                for result in search_results[:max_results]:
                    try:
                        link = result.find_element(By.CSS_SELECTOR, ".mw-search-result-heading a")
                        title = link.text.strip()
                        url = link.get_attribute("href")
                        
                        # Open the article in a new window
                        self.driver.execute_script(f'window.open("{url}");')
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        
                        WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_element_located((By.ID, "content"))
                        )
                        
                        article_content = self._extract_article_content()
                        
                        if article_content and len(article_content) > 100:
                            references.append({
                                "url": url,
                                "title": title,
                                "content": article_content
                            })
                            count += 1
                            logger.info(f"Extracted content from {title}")
                        
                        # Close the article window and switch back
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        
                    except Exception as e:
                        logger.error(f"Error processing search result: {e}")
                        # If we have multiple windows open, close extras
                        if len(self.driver.window_handles) > 1:
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
            
            logger.info(f"Found {len(references)} reference sources")
            return references
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return references
    
    def _extract_article_content(self):
        """Extract content from a Wikipedia article"""
        try:
            # Get article introduction (first paragraph)
            intro_element = self.driver.find_element(By.CSS_SELECTOR, "#mw-content-text p:not(.mw-empty-elt)")
            introduction = intro_element.text if intro_element else ""
            
            # Get article content
            content_element = self.driver.find_element(By.ID, "mw-content-text")
            content = content_element.text if content_element else ""
            
            # Combine and clean
            full_content = introduction + "\n\n" + content
            return full_content
            
        except Exception as e:
            logger.error(f"Error extracting article content: {e}")
            return ""

def main():
    parser = argparse.ArgumentParser(description="Web Scraper for Reference Content")
    parser.add_argument("--subject", required=True, help="Subject to search for (e.g., 'Computer Science')")
    parser.add_argument("--output", default="data/references.json", help="Output JSON file path")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results to collect")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for web operations in seconds")
    parser.add_argument("--sample", default=None, help="Sample file path to extract keywords from")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in visible mode")
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Initialize and start web scraper
    scraper = WebScraper(headless=not args.no_headless)
    if scraper.start():
        try:
            # Search for references
            references = scraper.search_for_references(args.subject, args.max_results, args.timeout)
            
            # Save results
            if references:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(references, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(references)} reference sources to {args.output}")
            else:
                # Create mock reference if none found
                mock_references = [{
                    "url": "https://example.com/mock-reference",
                    "title": f"Mock Reference for {args.subject}",
                    "content": f"This is a mock reference for {args.subject}. In a real scenario, this would contain information relevant to the subject."
                }]
                
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(mock_references, f, ensure_ascii=False, indent=2)
                logger.warning(f"No references found. Created mock reference in {args.output}")
                
        except Exception as e:
            logger.error(f"Error in web scraper: {e}")
        finally:
            # Stop web scraper
            scraper.stop()
    else:
        logger.error("Failed to initialize web scraper")
        
        # Create mock reference as fallback
        mock_references = [{
            "url": "https://example.com/mock-reference",
            "title": f"Mock Reference for {args.subject}",
            "content": f"This is a mock reference for {args.subject}. In a real scenario, this would contain information relevant to the subject."
        }]
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(mock_references, f, ensure_ascii=False, indent=2)
        logger.warning(f"Created mock reference in {args.output}")

if __name__ == "__main__":
    main()
