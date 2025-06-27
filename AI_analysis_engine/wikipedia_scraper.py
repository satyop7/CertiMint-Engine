#!/usr/bin/env python3
import os
import sys
import json
import argparse
import logging
import time
import random
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wikipedia_scraper')

class WikipediaScraper:
    def __init__(self, max_results=3):
        """Initialize Wikipedia scraper using requests"""
        self.max_results = max_results
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'
        }
        
        logger.info("Using requests-based Wikipedia scraper")
    
    def search_wikipedia(self, query):
        """Search Wikipedia for articles related to the query"""
        logger.info(f"Searching Wikipedia for: '{query}'")
        
        # First try direct article access by constructing the URL
        direct_url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
        try:
            response = requests.get(direct_url, headers=self.headers, timeout=10)
            if response.status_code == 200 and "Wikipedia does not have an article with this exact name" not in response.text:
                logger.info(f"Direct article found: {direct_url}")
                return [direct_url]
        except Exception as e:
            logger.warning(f"Error checking direct URL: {e}")
        
        # Try search page if direct article failed
        search_url = f"https://en.wikipedia.org/w/index.php?search={quote(query)}&title=Special:Search"
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                # Parse search results
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.select('.mw-search-result-heading a')
                
                urls = []
                for result in search_results[:self.max_results]:
                    url = "https://en.wikipedia.org" + result['href']
                    logger.info(f"Found result: {result.text.strip()} - {url}")
                    urls.append(url)
                
                if not urls:
                    logger.warning("No search results found")
                
                return urls
            else:
                logger.error(f"Search request failed with status code: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error during Wikipedia search: {e}")
            return []
    
    def scrape_article(self, url):
        """Scrape content from a Wikipedia article using requests"""
        logger.info(f"Scraping article: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch article: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get article title
            title_element = soup.find(id='firstHeading')
            title = title_element.get_text().strip() if title_element else "Unknown Title"
            
            # Get introduction paragraphs
            content_div = soup.select_one('#mw-content-text')
            intro_paragraphs = []
            if content_div:
                main_div = content_div.find('div', class_='mw-parser-output')
                if main_div:
                    for p in main_div.find_all('p', recursive=False)[:4]:  # Get first few paragraphs
                        text = p.get_text().strip()
                        if text and len(text) > 10:  # Avoid empty or very short paragraphs
                            intro_paragraphs.append(text)
            
            introduction = ' '.join(intro_paragraphs)
            
            # Extract infobox data
            infobox = {}
            infobox_table = soup.select_one('.infobox')
            if infobox_table:
                for row in infobox_table.select('tr'):
                    th = row.select_one('th')
                    td = row.select_one('td')
                    if th and td:
                        infobox[th.get_text().strip()] = td.get_text().strip()
            
            # Get sections and their content
            sections = []
            section_content = {}
            
            if main_div:
                for heading in main_div.find_all(['h2', 'h3'])[:7]:  # Limit to first 7 headings
                    span = heading.select_one('.mw-headline')
                    if span:
                        section_title = span.get_text().strip()
                        
                        # Skip irrelevant sections
                        if section_title in ['See also', 'References', 'External links', 'Notes', 'Citations']:
                            continue
                            
                        sections.append(section_title)
                        
                        # Get section content (paragraphs following this heading until next heading)
                        content = []
                        for sibling in heading.next_siblings:
                            if sibling.name in ['h2', 'h3', 'h4']:
                                break
                            if sibling.name == 'p':
                                text = sibling.get_text().strip()
                                if text:
                                    content.append(text)
                        
                        section_content[section_title] = ' '.join(content[:3])  # Limit to first 3 paragraphs
            
            return {
                'title': title,
                'url': url,
                'introduction': introduction,
                'infobox': infobox,
                'sections': sections,
                'section_content': section_content
            }
        except Exception as e:
            logger.error(f"Error scraping article with requests: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Wikipedia Scraper")
    parser.add_argument("--query", required=True, help="Search query for Wikipedia")
    parser.add_argument("--output", default="data/references.json", help="Output JSON file path")
    parser.add_argument("--max-results", type=int, default=3, help="Maximum number of articles to scrape")
    args = parser.parse_args()
    
    logger.info(f"Starting Wikipedia scraper for query: '{args.query}'")
    logger.info(f"Max results: {args.max_results}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    try:
        # Initialize scraper
        scraper = WikipediaScraper(max_results=args.max_results)
        
        # Search Wikipedia
        article_urls = scraper.search_wikipedia(args.query)
        
        # Scrape articles
        results = []
        for url in article_urls:
            article_data = scraper.scrape_article(url)
            if article_data:
                results.append(article_data)
            
            # Add small delay between requests to be polite
            time.sleep(random.uniform(1, 2))
        
        # Save results to file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully scraped {len(results)} articles")
        logger.info(f"Results saved to: {args.output}")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        
        # Create mock reference data as fallback
        mock_results = [{
            "title": args.query,
            "url": f"https://en.wikipedia.org/wiki/{args.query.replace(' ', '_')}",
            "introduction": f"This is a mock reference source for {args.query}. The content includes key terms and concepts related to this subject.",
            "infobox": {},
            "sections": ["Overview", "History", "Applications"],
            "section_content": {
                "Overview": f"Overview of {args.query} including definitions and key concepts.",
                "History": f"Historical development of {args.query} and major milestones.",
                "Applications": f"Practical applications and implementations of {args.query} in various fields."
            }
        }]
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(mock_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created mock reference data in {args.output}")
        sys.exit(1)

if __name__ == "__main__":
    main()
