"""
Amazon Product Scraper

This script scrapes product information from Amazon while implementing best practices:
- Random delays between requests: Prevents detection by mimicking human browsing patterns
- Rotating user agents: Changes browser identification to avoid blocking
- Proxy rotation: Uses different IP addresses to distribute requests
- Respect for robots.txt: Follows website's crawling rules
- Error handling and retries: Gracefully handles failures and attempts recovery
- Rate limiting: Controls request frequency to avoid overloading the server
- Logging: Records all activities for monitoring and debugging

The scraper extracts comprehensive product details including:
- Basic information (title, price, availability)
- Ratings and reviews
- Product descriptions and features
- Technical details and specifications
- Product images

It also provides analytical capabilities to understand search results patterns,
price distributions, and common product features.

Usage:
    python amazon_scraper.py

Output:
    - JSON file with complete product data
    - CSV file with flattened product data for easy analysis
    - JSON analysis file with insights about the products
"""

import requests
import time
import random
import logging
import os
import json
import csv
import re
from urllib.parse import urlparse, urljoin, quote_plus
from bs4 import BeautifulSoup
import concurrent.futures
from datetime import datetime
from fake_useragent import UserAgent
from requests.exceptions import RequestException, Timeout, ConnectionError, ProxyError
import urllib.robotparser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='amazon_scraper.log',
    filemode='a'
)
logger = logging.getLogger('amazon_scraper')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Constants
BASE_URL = "https://www.amazon.com"
SEARCH_URL = "https://www.amazon.com/s?k={}"
OUTPUT_DIR = "amazon_data"
MAX_RETRIES = 3          # Maximum number of retry attempts for failed requests
REQUEST_TIMEOUT = 15     # Request timeout in seconds
MAX_WORKERS = 5          # Number of parallel workers for concurrent operations

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class AmazonScraper:
    """
    Class to scrape Amazon product information with best practices
    
    This class provides a complete implementation for scraping Amazon product data
    while following ethical scraping practices and avoiding detection. It includes
    methods for searching products, extracting detailed information, and saving
    the results in multiple formats.
    """
    
    def __init__(self, use_proxies=True, respect_robots=True, delay_range=(3, 7)):
        """
        Initialize the scraper with configuration options
        
        Args:
            use_proxies (bool): Whether to use rotating proxies for requests
            respect_robots (bool): Whether to respect robots.txt crawling rules
            delay_range (tuple): Range for random delays between requests (min, max) in seconds
        """
        self.use_proxies = use_proxies
        self.respect_robots = respect_robots
        self.delay_range = delay_range
        self.proxies = [None]  # Start with no proxy
        self.user_agents = []
        self.session = requests.Session()
        self.robot_parser = None
        
        # Load proxies if needed
        if use_proxies:
            self.proxies = self.get_free_proxies()
        
        # Setup user agents
        try:
            self.ua = UserAgent()
        except:
            # Fallback user agents if fake_useragent fails
            self.ua = None
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            ]
        
        # Setup robots.txt parser
        if respect_robots:
            self.setup_robots_parser()
    
    def setup_robots_parser(self):
        """
        Initialize the robots.txt parser
        
        Fetches and parses the robots.txt file from Amazon to determine
        which pages can be legally crawled according to the site's policies.
        """
        self.robot_parser = urllib.robotparser.RobotFileParser()
        self.robot_parser.set_url(f"{BASE_URL}/robots.txt")
        try:
            self.robot_parser.read()
            logger.info("Successfully parsed robots.txt")
        except Exception as e:
            logger.warning(f"Failed to parse robots.txt: {e}")
            self.robot_parser = None
    
    def get_free_proxies(self, max_proxies=10):
        """
        Get a list of free proxies from multiple sources
        
        Scrapes several proxy listing websites to find working proxies,
        validates them, and returns a list of reliable options that can
        be used for rotation during scraping.
        
        Args:
            max_proxies (int): Maximum number of proxies to return
            
        Returns:
            list: List of working proxy URLs
        """
        logger.info("Fetching free proxies...")
        
        # Initialize with a direct connection option
        proxies = [None]
        
        proxy_sources = [
            'https://www.sslproxies.org/',
            'https://free-proxy-list.net/',
            'https://www.us-proxy.org/'
        ]
        
        all_proxies = []
        
        # Scrape proxies from sources
        for source in proxy_sources:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(source, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for table in soup.find_all('table'):
                        for row in table.find_all('tr'):
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                try:
                                    ip = cells[0].text.strip()
                                    port = cells[1].text.strip()
                                    
                                    if ip and port and ip.count('.') == 3:
                                        all_proxies.append(f"http://{ip}:{port}")
                                except:
                                    continue
            
            except Exception as e:
                logger.warning(f"Error fetching proxies from {source}: {e}")
        
        logger.info(f"Found {len(all_proxies)} potential proxies")
        
        # Test proxies in parallel
        working_proxies = []
        
        def test_proxy(proxy):
            try:
                test_url = 'https://httpbin.org/ip'
                proxies = {'http': proxy, 'https': proxy}
                response = requests.get(test_url, proxies=proxies, timeout=5)
                
                if response.status_code == 200:
                    return proxy
            except:
                pass
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(test_proxy, all_proxies))
        
        working_proxies = [proxy for proxy in results if proxy]
        logger.info(f"Validated {len(working_proxies)} working proxies")
        
        # Combine with the None option (direct connection)
        proxies.extend(working_proxies)
        
        return proxies[:max_proxies]
    
    def get_random_user_agent(self):
        """
        Get a random user agent
        
        Returns a randomly selected user agent string to use in HTTP requests,
        helping to avoid detection by varying the browser identification.
        
        Returns:
            str: A random user agent string
        """
        if self.ua:
            return self.ua.random
        else:
            return random.choice(self.user_agents)
    
    def get_request_headers(self):
        """
        Generate headers for the HTTP request
        
        Creates a dictionary of HTTP headers that mimic a real browser,
        using a random user agent and adding common browser headers.
        
        Returns:
            dict: Headers to use in HTTP requests
        """
        user_agent = self.get_random_user_agent()
        
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def can_fetch(self, url):
        """
        Check if URL can be fetched according to robots.txt
        
        Verifies if the given URL is allowed to be crawled according to
        the website's robots.txt file, respecting the site's crawling policies.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if allowed, False if disallowed
        """
        if not self.respect_robots or not self.robot_parser:
            return True
        
        user_agent = self.get_random_user_agent()
        try:
            can_fetch = self.robot_parser.can_fetch(user_agent, url)
            if not can_fetch:
                logger.warning(f"robots.txt disallows: {url}")
            return can_fetch
        except:
            return True
    
    def make_request(self, url, retries=MAX_RETRIES):
        """
        Make an HTTP request with retries and rotating proxies
        
        Sends an HTTP request to the provided URL, implementing multiple
        best practices:
        - Checking robots.txt compliance
        - Adding random delays between requests
        - Using rotating proxies and user agents
        - Implementing retries with exponential backoff
        - Detecting blocking or CAPTCHA challenges
        
        Args:
            url (str): URL to request
            retries (int): Number of retry attempts
            
        Returns:
            tuple: (success, response_or_error)
        """
        if not self.can_fetch(url):
            return False, "Blocked by robots.txt"
        
        # Random delay before request - increasing delay range
        time.sleep(random.uniform(self.delay_range[0]*1.5, self.delay_range[1]*2))
        
        # Track failed proxies during this request
        failed_proxies = set()
        
        # Try each proxy until success or out of retries
        for attempt in range(retries):
            # Select a proxy and UA, avoiding recently failed ones
            available_proxies = [p for p in self.proxies if p not in failed_proxies]
            
            # If all proxies failed, reset and increase delay
            if not available_proxies:
                available_proxies = self.proxies
                time.sleep(random.uniform(5, 10))  # Longer cooldown
            
            proxy = random.choice(available_proxies) if available_proxies else None
            headers = self.get_enhanced_headers(url)
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            
            try:
                logger.info(f"Request to {url} (Attempt {attempt+1}/{retries}, Proxy: {proxy})")
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                
                # Handle HTTP 202 status which Amazon sometimes uses for bot detection
                if response.status_code == 202:
                    logger.warning("Received HTTP 202 - Accepted but not fulfilled. Retrying with delay...")
                    if proxy:
                        failed_proxies.add(proxy)
                    time.sleep(random.uniform(10, 15))  # Longer delay for 202 responses
                    continue
                
                # Check if we've been blocked
                if response.status_code == 503 or "captcha" in response.text.lower():
                    logger.warning("Request blocked or CAPTCHA encountered")
                    if proxy:
                        failed_proxies.add(proxy)
                    continue
                
                if response.status_code == 200:
                    # Validate that we actually got product content
                    if "amazon" in response.text.lower() and len(response.text) > 5000:
                        return True, response
                    else:
                        logger.warning("Response too small or does not contain expected content")
                        if proxy:
                            failed_proxies.add(proxy)
                        continue
                
                logger.warning(f"HTTP Error: {response.status_code}")
                if proxy:
                    failed_proxies.add(proxy)
            
            except (ConnectionError, Timeout, ProxyError) as e:
                logger.warning(f"Request failed: {str(e)}")
                if proxy:
                    failed_proxies.add(proxy)
            
            # Exponential backoff after failure
            backoff_time = (attempt + 1) * random.uniform(self.delay_range[0], self.delay_range[1])
            logger.info(f"Backing off for {backoff_time:.2f} seconds")
            time.sleep(backoff_time)
        
        logger.error(f"All {retries} attempts failed for {url}")
        return False, f"Failed after {retries} attempts"
    
    def get_enhanced_headers(self, url):
        """
        Generate more realistic browser headers
        
        Returns headers that closely mimic a real browser session with
        referer, cookies, and other properties that help avoid detection.
        
        Args:
            url (str): URL being requested (for referer logic)
            
        Returns:
            dict: Enhanced headers for HTTP requests
        """
        user_agent = self.get_random_user_agent()
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # More realistic headers that mimic browser behavior
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/search?q=amazon+products',
            'Sec-Ch-Ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        # Add cookies if available from session
        if domain in self.session.cookies.list_domains():
            headers['Cookie'] = '; '.join([f"{c.name}={c.value}" for c in self.session.cookies])
        
        return headers

    def search_products(self, query, max_pages=1):
        """
        Search for products on Amazon with enhanced URL extraction
        
        Args:
            query (str): Search query
            max_pages (int): Maximum number of result pages to scrape
            
        Returns:
            list: List of product URLs
        """
        product_urls = set()  # Use set to avoid duplicates
        encoded_query = quote_plus(query)
        
        for page in range(1, max_pages + 1):
            # Construct URL with page number
            if page == 1:
                url = SEARCH_URL.format(encoded_query)
            else:
                url = f"{SEARCH_URL.format(encoded_query)}&page={page}"
            
            logger.info(f"Processing search page {page}/{max_pages}")
            success, response = self.make_request(url)
            
            if not success:
                logger.error(f"Failed to retrieve search page {page}: {response}")
                continue
            
            # Save response for debugging
            self._save_debug_html(response.text, f"search_page_{page}.html")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_urls = self._extract_product_urls_comprehensive(soup, page)
            
            if page_urls:
                product_urls.update(page_urls)
                logger.info(f"Found {len(page_urls)} product URLs on page {page}")
            else:
                logger.warning(f"No product URLs found on page {page}")
                # Save the HTML for manual inspection
                self._save_debug_html(response.text, f"failed_page_{page}.html")
        
        final_urls = list(product_urls)
        logger.info(f"Total unique product URLs found: {len(final_urls)}")
        return final_urls
    
    def _extract_product_urls_comprehensive(self, soup, page_num):
        """
        Comprehensive product URL extraction with multiple fallback strategies
        
        Args:
            soup: BeautifulSoup object
            page_num: Page number for debugging
            
        Returns:
            list: List of product URLs found
        """
        product_urls = set()
        
        # Strategy 1: Primary Amazon search result selectors
        primary_selectors = [
            'div[data-component-type="s-search-result"]',
            'div[data-component-type="s-product-image"]',
            'div.s-result-item[data-asin]',
            'div[data-asin]:not([data-asin=""])',
            'div.sg-col-4-of-12.s-result-item',
            'div[data-uuid]'
        ]
        
        for selector in primary_selectors:
            cards = soup.select(selector)
            if cards:
                logger.info(f"Found {len(cards)} product cards using selector: {selector}")
                
                for card in cards:
                    urls = self._extract_urls_from_card(card)
                    product_urls.update(urls)
                
                if product_urls:
                    break  # Stop if we found URLs with this selector
        
        # Strategy 2: Link-based extraction with product patterns
        if not product_urls:
            logger.info("Primary selectors failed, trying link-based extraction")
            
            # Look for all links that match Amazon product patterns
            all_links = soup.find_all('a', href=True)
            product_patterns = [
                re.compile(r'/dp/[A-Z0-9]{10}'),
                re.compile(r'/gp/product/[A-Z0-9]{10}'),
                re.compile(r'/exec/obidos/ASIN/[A-Z0-9]{10}'),
                re.compile(r'amazon\.com.*?/dp/[A-Z0-9]{10}')
            ]
            
            for link in all_links:
                href = link.get('href', '')
                for pattern in product_patterns:
                    if pattern.search(href):
                        full_url = urljoin(BASE_URL, href)
                        # Clean URL parameters except essential ones
                        clean_url = self._clean_product_url(full_url)
                        if clean_url:
                            product_urls.add(clean_url)
                            logger.debug(f"Found product URL via pattern: {clean_url}")
        
        # Strategy 3: ASIN-based extraction
        if not product_urls:
            logger.info("Link extraction failed, trying ASIN-based extraction")
            
            # Look for data-asin attributes
            asin_elements = soup.find_all(attrs={'data-asin': True})
            for element in asin_elements:
                asin = element.get('data-asin')
                if asin and len(asin) == 10 and asin.isalnum():
                    product_url = f"{BASE_URL}/dp/{asin}"
                    product_urls.add(product_url)
                    logger.debug(f"Found product via ASIN: {asin}")
        
        # Strategy 4: Text-based ASIN extraction
        if not product_urls:
            logger.info("ASIN extraction failed, trying text-based extraction")
            
            # Look for ASINs in text content
            page_text = soup.get_text()
            asin_pattern = re.compile(r'\b[A-Z0-9]{10}\b')
            potential_asins = asin_pattern.findall(page_text)
            
            for asin in set(potential_asins):  # Remove duplicates
                # Basic validation - ASINs usually start with B or have mixed case
                if asin.startswith('B') or not asin.isdigit():
                    product_url = f"{BASE_URL}/dp/{asin}"
                    product_urls.add(product_url)
                    logger.debug(f"Found potential product via text ASIN: {asin}")
        
        return list(product_urls)
    
    def _extract_urls_from_card(self, card):
        """Extract product URLs from a product card element"""
        urls = set()
        
        # Multiple link extraction strategies for the card
        link_selectors = [
            'h2 a',
            'h2 a.a-link-normal',
            'a[title]',
            'a[href*="/dp/"]',
            'a[href*="/gp/product/"]',
            '.s-image a',
            '.a-link-normal',
            'a.a-link-normal'
        ]
        
        for selector in link_selectors:
            links = card.select(selector)
            for link in links:
                href = link.get('href')
                if href and ('/dp/' in href or '/gp/product/' in href):
                    full_url = urljoin(BASE_URL, href)
                    clean_url = self._clean_product_url(full_url)
                    if clean_url:
                        urls.add(clean_url)
        
        return urls
    
    def _clean_product_url(self, url):
        """Clean and validate a product URL"""
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            parsed = urlparse(url)
            
            # Must be an Amazon URL
            if 'amazon.com' not in parsed.netloc:
                return None
            
            # Must have product identifier
            if not ('/dp/' in parsed.path or '/gp/product/' in parsed.path):
                return None
            
            # Keep only essential parameters
            query_params = parse_qs(parsed.query)
            essential_params = {}
            
            # Keep ref parameter if present (helps with tracking)
            if 'ref' in query_params:
                essential_params['ref'] = query_params['ref'][0]
            
            new_query = urlencode(essential_params) if essential_params else ''
            
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                ''  # Remove fragment
            ))
            
            return clean_url
            
        except Exception:
            return None
    
    def _save_debug_html(self, html_content, filename):
        """Save HTML content for debugging purposes"""
        try:
            debug_dir = os.path.join(OUTPUT_DIR, 'debug')
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            filepath = os.path.join(debug_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.debug(f"Saved debug HTML: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to save debug HTML: {e}")

    def extract_product_details(self, url):
        """
        Extract details from a product page
        
        Scrapes comprehensive information from an Amazon product page, including:
        - Basic information (title, price, availability)
        - Ratings and reviews
        - Product descriptions and features
        - Technical details and specifications
        - Product images
        
        The extraction adapts to different page layouts and handles missing
        information gracefully.
        
        Args:
            url (str): Product URL
            
        Returns:
            dict: Product details or None if failed
        """
        # Try with the fallback Selenium-based extraction if available
        if hasattr(self, 'extract_with_selenium') and callable(getattr(self, 'extract_with_selenium')):
            try:
                selenium_result = self.extract_with_selenium(url)
                if selenium_result:
                    return selenium_result
                # If Selenium fails, fall back to requests-based method
                logger.warning("Selenium extraction failed, trying with requests")
            except Exception as e:
                logger.warning(f"Selenium extraction error: {str(e)}. Falling back to requests")
        
        success, response = self.make_request(url)
        
        if not success:
            logger.error(f"Failed to retrieve product page: {response}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Basic product information
            product = {
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Title
            title_element = soup.select_one('#productTitle')
            if title_element:
                product['title'] = title_element.get_text(strip=True)
            
            # Price - This is complex in Amazon as there are many price formats
            price = None
            price_elements = [
                soup.select_one('span.a-price .a-offscreen'),
                soup.select_one('#priceblock_ourprice'),
                soup.select_one('#priceblock_dealprice'),
                soup.select_one('.a-price .a-offscreen')
            ]
            
            for element in price_elements:
                if element:
                    price_text = element.get_text(strip=True)
                    price = price_text
                    break
            
            product['price'] = price
            
            # Availability
            availability_element = soup.select_one('#availability')
            if availability_element:
                product['availability'] = availability_element.get_text(strip=True)
            
            # Rating
            rating_element = soup.select_one('#acrPopover')
            if rating_element and rating_element.has_attr('title'):
                rating_text = rating_element['title']
                match = re.search(r'(\d+(\.\d+)?) out of 5 stars', rating_text)
                if match:
                    product['rating'] = float(match.group(1))
            
            # Number of reviews
            reviews_element = soup.select_one('#acrCustomerReviewText')
            if reviews_element:
                reviews_text = reviews_element.get_text(strip=True)
                match = re.search(r'([\d,]+) ratings', reviews_text)
                if match:
                    product['reviews_count'] = match.group(1).replace(',', '')
            
            # Product description
            description = ""
            desc_element = soup.select_one('#productDescription')
            if desc_element:
                description = desc_element.get_text(strip=True)
            
            # Feature bullets
            features = []
            feature_elements = soup.select('#feature-bullets ul li')
            for feature in feature_elements:
                feature_text = feature.get_text(strip=True)
                if feature_text:
                    features.append(feature_text)
            
            product['features'] = features
            product['description'] = description
            
            # Product details from product information section
            details = {}
            detail_elements = soup.select('#productDetails_detailBullets_sections1 tr')
            for row in detail_elements:
                header = row.select_one('th')
                value = row.select_one('td')
                if header and value:
                    key = header.get_text(strip=True).rstrip(':')
                    details[key] = value.get_text(strip=True)
            
            # Additional product details from detailBullets
            bullet_elements = soup.select('#detailBullets_feature_div li .a-text-bold')
            for element in bullet_elements:
                key_element = element
                value_element = element.find_next_sibling()
                
                if key_element and value_element:
                    key = key_element.get_text(strip=True).rstrip(':')
                    value = value_element.get_text(strip=True)
                    details[key] = value
            
            product['details'] = details
            
            # Images
            images = []
            image_elements = soup.select('#imgTagWrapperId img, #imageBlock img')
            for img in image_elements:
                if img.has_attr('src'):
                    images.append(img['src'])
                elif img.has_attr('data-old-hires'):
                    images.append(img['data-old-hires'])
            
            # Sometimes images are in a data attribute containing JSON
            image_data_element = soup.select_one('[data-a-dynamic-image]')
            if image_data_element and image_data_element.has_attr('data-a-dynamic-image'):
                try:
                    image_data = json.loads(image_data_element['data-a-dynamic-image'])
                    for image_url in image_data.keys():
                        if image_url not in images:
                            images.append(image_url)
                except:
                    pass
            
            product['images'] = images
            
            return product
        
        except Exception as e:
            logger.error(f"Error extracting product details: {e}")
            return None
    
    def analyze_search_rankings(self, products, search_query):
        """
        Analyze product rankings based on the search query
        
        Processes the scraped product data to extract insights and patterns:
        - Identifies top-rated products
        - Calculates price statistics (min, max, average)
        - Analyzes rating distribution
        - Extracts common features and keywords
        
        This analysis helps understand product trends and competitive positioning
        within the search results.
        
        Args:
            products (list): List of scraped products
            search_query (str): The original search query
            
        Returns:
            dict: Analysis of top-ranked products
        """
        if not products:
            return {"error": "No products found"}
        
        # Extract key metrics for analysis
        analysis = {
            "search_query": search_query,
            "total_products": len(products),
            "top_rated_products": [],
            "price_range": {
                "min": None,
                "max": None,
                "average": 0
            },
            "rating_distribution": {},
            "common_features": {}
        }
        
        # Sort by rating for top products
        rated_products = [p for p in products if 'rating' in p and p['rating']]
        rated_products.sort(key=lambda x: x['rating'], reverse=True)
        
        # Get top 5 rated products
        for product in rated_products[:5]:
            analysis["top_rated_products"].append({
                "title": product.get('title', 'Unknown'),
                "rating": product.get('rating', 'N/A'),
                "price": product.get('price', 'N/A'),
                "reviews_count": product.get('reviews_count', 'N/A'),
                "url": product.get('url', 'N/A')
            })
        
        # Calculate price statistics
        prices = []
        for product in products:
            if 'price' in product and product['price']:
                try:
                    # Extract numeric price
                    price_text = product['price']
                    price_value = float(re.sub(r'[^\d.]', '', price_text))
                    prices.append(price_value)
                except:
                    pass
        
        if prices:
            analysis["price_range"]["min"] = min(prices)
            analysis["price_range"]["max"] = max(prices)
            analysis["price_range"]["average"] = sum(prices) / len(prices)
        
        # Analyze ratings distribution
        for product in products:
            if 'rating' in product and product['rating']:
                rating = round(product['rating'] * 2) / 2  # Round to nearest 0.5
                analysis["rating_distribution"][rating] = analysis["rating_distribution"].get(rating, 0) + 1
        
        # Analyze common features
        feature_count = {}
        for product in products:
            if 'features' in product:
                for feature in product['features']:
                    # Extract key terms from features
                    for term in re.findall(r'\b\w{4,}\b', feature.lower()):
                        feature_count[term] = feature_count.get(term, 0) + 1
        
        # Get top 10 common features
        sorted_features = sorted(feature_count.items(), key=lambda x: x[1], reverse=True)
        analysis["common_features"] = dict(sorted_features[:10])
        
        return analysis
    
    def scrape_products(self, query, max_pages=1, max_products=None):
        """
        Search for and scrape products
        
        Coordinates the complete scraping process:
        1. Searches for products matching the query
        2. Limits results to the requested number if specified
        3. Sequentially extracts details from each product page
        
        This is the main entry point for scraping operations.
        
        Args:
            query (str): Search query
            max_pages (int): Maximum search result pages to scrape
            max_products (int): Maximum number of products to scrape
            
        Returns:
            list: List of product details
        """
        logger.info(f"Searching for products: {query}")
        product_urls = self.search_products(query, max_pages)
        
        if max_products:
            product_urls = product_urls[:max_products]
        
        logger.info(f"Found {len(product_urls)} product URLs")
        
        # Scrape products sequentially to avoid overwhelming the server
        products = []
        for i, url in enumerate(product_urls):
            logger.info(f"Scraping product {i+1}/{len(product_urls)}")
            product = self.extract_product_details(url)
            if product:
                products.append(product)
        
        return products
    
    def save_to_json(self, products, filename):
        """
        Save products to a JSON file
        
        Stores the complete product data in JSON format, preserving
        all nested structures and relationships. This format is ideal
        for further programmatic processing.
        
        Args:
            products (list): List of product dictionaries
            filename (str): Name of the output file
        """
        if not products:
            logger.warning("No products to save")
            return
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(products)} products to {filepath}")
    
    def save_to_csv(self, products, filename):
        """
        Save products to a CSV file
        
        Converts the product data to a flattened CSV format suitable for
        spreadsheet analysis. Handles nested structures by creating separate
        columns with prefixes or joining array values into comma-separated strings.
        
        Args:
            products (list): List of product dictionaries
            filename (str): Name of the output file
        """
        if not products:
            logger.warning("No products to save")
            return
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Get all possible fields
        all_fields = set()
        for product in products:
            all_fields.update(product.keys())
            if 'details' in product and isinstance(product['details'], dict):
                all_fields.update(f"detail_{k}" for k in product['details'].keys())
        
        # Remove nested fields that will be flattened
        for field in ['details', 'features', 'images']:
            if field in all_fields:
                all_fields.remove(field)
        
        # Convert to list and sort
        fieldnames = sorted(list(all_fields))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                flat_product = {k: v for k, v in product.items() 
                                if k != 'details' and k != 'features' and k != 'images'}
                
                # Flatten details
                if 'details' in product and isinstance(product['details'], dict):
                    for k, v in product['details'].items():
                        flat_product[f"detail_{k}"] = v
                
                # Flatten arrays to strings
                if 'features' in product:
                    flat_product['features_text'] = ', '.join(product['features'])
                
                if 'images' in product:
                    flat_product['images_text'] = ', '.join(product['images'])
                
                writer.writerow(flat_product)
        
        logger.info(f"Saved {len(products)} products to {filepath}")

def main():
    """
    Main function to run the scraper
    
    Controls the complete scraping workflow:
    1. Initializes the scraper with desired configuration
    2. Gets user input for the search query and parameters
    3. Executes the scraping process
    4. Saves results in multiple formats (JSON, CSV)
    5. Performs analysis on the search results
    6. Displays summary information to the user
    
    This function is the entry point when running the script directly.
    """
    logger.info("Starting Amazon scraper")
    
    # Create scraper
    scraper = AmazonScraper(use_proxies=True, respect_robots=True)
    
    # Get search query
    search_query = input("Enter product search query: ")
    max_pages = int(input("Maximum number of pages to scrape (1-20): ") or "1")
    max_products = int(input("Maximum number of products to scrape (default all): ") or "0") or None
    
    # Scrape products
    products = scraper.scrape_products(search_query, max_pages, max_products)
    
    if products:
        # Generate filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_query = re.sub(r'[^\w]', '_', search_query.lower())
        json_filename = f"{sanitized_query}_{timestamp}.json"
        csv_filename = f"{sanitized_query}_{timestamp}.csv"
        
        # Save results
        scraper.save_to_json(products, json_filename)
        scraper.save_to_csv(products, csv_filename)
        
        # Analyze search rankings
        analysis = scraper.analyze_search_rankings(products, search_query)
        analysis_filename = f"{sanitized_query}_analysis_{timestamp}.json"
        
        # Save analysis
        with open(os.path.join(OUTPUT_DIR, analysis_filename), 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\nScraping completed successfully!")
        print(f"Found {len(products)} products")
        print(f"Results saved to:")
        print(f"  - {os.path.join(OUTPUT_DIR, json_filename)}")
        print(f"  - {os.path.join(OUTPUT_DIR, csv_filename)}")
        print(f"  - {os.path.join(OUTPUT_DIR, analysis_filename)}")
        
        # Display top products in console
        print("\nTop 5 ranked products for this search:")
        for i, product in enumerate(analysis["top_rated_products"]):
            print(f"{i+1}. {product['title']}")
            print(f"   Rating: {product['rating']} ⭐ ({product['reviews_count']} reviews)")
            print(f"   Price: {product['price']}")
            print()
    else:
        print("\nNo products found or scraping failed")

if __name__ == "__main__":
    main()
