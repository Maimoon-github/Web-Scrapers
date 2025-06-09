"""
Enhanced Amazon Scraper with Better Anti-Detection

This version implements additional strategies to avoid detection:
- Session warming
- Progressive delays
- Browser fingerprint simulation
- Cookie management
"""

import time
import random
import logging
import re
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
from amazon_scraper import AmazonScraper

# Set up logger with console handler
logger = logging.getLogger('enhanced_amazon_scraper')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class EnhancedAmazonScraper(AmazonScraper):
    """Enhanced Amazon scraper with better anti-detection measures"""
    
    def __init__(self, use_proxies=False, respect_robots=True, delay_range=(5, 12)):
        super().__init__(use_proxies, respect_robots, delay_range)
        self.session_warmed = False
        self.request_count = 0
        
    def warm_up_session(self):
        """Warm up the session by making some initial requests"""
        if self.session_warmed:
            return
            
        logger.info("Warming up session...")
        
        # Visit Amazon homepage first
        homepage_success, _ = self.make_request("https://www.amazon.com")
        if homepage_success:
            logger.info("✓ Homepage visit successful")
            time.sleep(random.uniform(3, 6))
        
        # Visit a category page
        category_success, _ = self.make_request("https://www.amazon.com/gp/bestsellers")
        if category_success:
            logger.info("✓ Category page visit successful")
            time.sleep(random.uniform(2, 5))
        
        self.session_warmed = True
        logger.info("Session warm-up completed")
    
    def get_enhanced_headers(self, url):
        """Get enhanced headers with more realistic browser simulation"""
        headers = super().get_enhanced_headers(url)
        
        # Add more browser-like headers
        additional_headers = {
            'Accept-CH': 'Sec-CH-UA, Sec-CH-UA-Mobile, Sec-CH-UA-Platform',
            'Sec-Purpose': 'navigate',
            'Sec-GPC': '1',
            'Pragma': 'no-cache',
        }
        
        # Randomly include some optional headers
        if random.random() > 0.3:
            headers.update(additional_headers)
        
        # Simulate different viewport sizes
        viewport_sizes = ['1920,1080', '1366,768', '1536,864', '1440,900']
        headers['Viewport-Width'] = random.choice(viewport_sizes).split(',')[0]
        
        return headers
    
    def make_request(self, url, retries=3):
        """Enhanced request method with better detection avoidance"""
        self.request_count += 1
        
        # Warm up session if not done
        if not self.session_warmed and self.request_count == 1:
            self.warm_up_session()
        
        # Progressive delays based on request count
        if self.request_count > 5:
            base_delay = random.uniform(8, 15)
        elif self.request_count > 2:
            base_delay = random.uniform(5, 10)
        else:
            base_delay = random.uniform(3, 6)
        
        logger.info(f"Request #{self.request_count}, waiting {base_delay:.1f}s")
        time.sleep(base_delay)
        
        # Use the parent's make_request but with no proxies initially
        # Amazon often blocks proxy requests more aggressively
        original_proxies = self.proxies
        self.proxies = [None]  # Force direct connection
        
        try:
            success, response = super().make_request(url, retries)
            
            # If direct connection fails, try with proxies
            if not success and original_proxies and len(original_proxies) > 1:
                logger.info("Direct connection failed, trying with proxies...")
                self.proxies = original_proxies
                success, response = super().make_request(url, retries)
            
            return success, response
            
        finally:
            self.proxies = original_proxies
    
    def search_products(self, query, max_pages=1):
        """Enhanced search with better error handling"""
        logger.info(f"Enhanced search for: {query}")
        
        # Try the standard search first
        try:
            product_urls = super().search_products(query, max_pages)
            
            # Filter out advertisement URLs
            filtered_urls = []
            for url in product_urls:
                # Check if it's an ad URL (contains aax-us or /gp/slredirect/)
                if 'aax-us' in url or '/gp/slredirect/' in url:
                    logger.info(f"Filtering advertisement URL: {url[:60]}...")
                    
                    # Try to extract the real product URL
                    match = re.search(r'amazon\.com/([^/]+/)?dp/([A-Z0-9]{10})', url)
                    if match:
                        asin = match.group(2)
                        clean_url = f"https://www.amazon.com/dp/{asin}"
                        logger.info(f"Extracted clean URL: {clean_url}")
                        filtered_urls.append(clean_url)
                else:
                    filtered_urls.append(url)
            
            # If we lost all URLs in filtering, return the originals
            if not filtered_urls and product_urls:
                logger.warning("All URLs were filtered as ads, using original URLs")
                return product_urls
                
            logger.info(f"Filtered {len(product_urls) - len(filtered_urls)} advertisement URLs")
            return filtered_urls
            
        except Exception as e:
            logger.error(f"Standard search failed: {e}")
            
            # Fallback: Try with different search URL format
            logger.info("Trying fallback search method...")
            return self._fallback_search(query, max_pages)
    
    def _fallback_search(self, query, max_pages):
        """Fallback search method with different URL structure"""
        product_urls = []
        
        # Try different Amazon search formats
        search_formats = [
            "https://www.amazon.com/s?k={}&ref=sr_pg_{}",
            "https://www.amazon.com/s?field-keywords={}&page={}",
            "https://www.amazon.com/s?url=search-alias%3Daps&field-keywords={}&page={}"
        ]
        
        for page in range(1, max_pages + 1):
            for search_format in search_formats:
                try:
                    if "{}&ref=" in search_format:
                        url = search_format.format(quote_plus(query), page)
                    else:
                        url = search_format.format(quote_plus(query), page)
                    
                    success, response = self.make_request(url)
                    
                    if success:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_urls = self._extract_product_urls_comprehensive(soup, page)
                        
                        if page_urls:
                            product_urls.extend(page_urls)
                            logger.info(f"Fallback method found {len(page_urls)} URLs on page {page}")
                            break  # Success with this format, continue to next page
                        
                except Exception as e:
                    logger.warning(f"Fallback search attempt failed: {e}")
                    continue
        
        # Filter out advertisement URLs
        clean_urls = []
        for url in set(product_urls):
            if 'aax-us' not in url and '/gp/slredirect/' not in url:
                clean_urls.append(url)
            else:
                # Extract ASIN from ad URL if possible
                match = re.search(r'amazon\.com/([^/]+/)?dp/([A-Z0-9]{10})', url)
                if match:
                    asin = match.group(2)
                    clean_url = f"https://www.amazon.com/dp/{asin}"
                    if clean_url not in clean_urls:
                        clean_urls.append(clean_url)
        
        return clean_urls
    
    def extract_product_details(self, url):
        """Enhanced product extraction with better handling of ad URLs"""
        # Handle advertisement URLs
        if 'aax-us' in url or '/gp/slredirect/' in url:
            logger.info("Cleaning advertisement URL for product extraction")
            
            # Extract ASIN from URL
            match = re.search(r'amazon\.com/([^/]+/)?dp/([A-Z0-9]{10})', url)
            if match:
                asin = match.group(2)
                url = f"https://www.amazon.com/dp/{asin}"
                logger.info(f"Using clean URL: {url}")
        
        # Handle redirects
        max_redirects = 3
        for _ in range(max_redirects):
            product = super().extract_product_details(url)
            
            # Check if we need to follow a redirect
            if product and 'url' in product and product['url'] != url:
                logger.info(f"Following redirect: {url} -> {product['url']}")
                url = product['url']
                continue
            
            return product
        
        logger.warning("Too many redirects when extracting product details")
        return None

def main():
    """Test the enhanced scraper"""
    print("Enhanced Amazon Scraper Test")
    print("=" * 40)
    
    # Create enhanced scraper
    scraper = EnhancedAmazonScraper(
        use_proxies=False,
        respect_robots=True,
        delay_range=(3, 8)
    )
    
    # Test search
    query = input("Enter search query: ")
    max_pages = int(input("Max pages (1-3): ") or "1")
    
    try:
        product_urls = scraper.search_products(query, max_pages)
        
        print(f"\nResults: {len(product_urls)} products found")
        
        if product_urls:
            print("\nFirst 5 URLs:")
            for i, url in enumerate(product_urls[:5]):
                print(f"{i+1}. {url}")
                
            print(f"\nExtracting product details...")
            products = []
            for url in product_urls:
                product = scraper.extract_product_details(url)
                if product:
                    products.append(product)
            
            if products:
                print(f"\nExporting {len(products)} products...")
                try:
                    from export_utils import export_data
                    exported_files = export_data(products, query)
                    
                    print("\nFiles exported successfully:")
                    for fmt, filepath in exported_files.items():
                        print(f"  - {fmt.upper()}: {filepath}")
                except ImportError:
                    print("\nExport utilities not available. Install required packages:")
                    print("pip install fpdf xlsxwriter pandas openpyxl")
            else:
                print("No product details could be extracted")
        else:
            print("No products found. Check debug files in amazon_data/debug/")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
