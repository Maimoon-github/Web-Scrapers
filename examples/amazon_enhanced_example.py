"""
Enhanced Amazon Scraper Example

This example demonstrates how to use the enhanced Amazon scraper
with Selenium integration for more reliable results.
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to path to import our package
sys.path.append(str(Path(__file__).parent.parent))

from amazon_scraper import AmazonScraper, extend_with_selenium

# Configure logging to console for this example
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

def main():
    """
    Main function to demonstrate the enhanced scraper
    """
    print("Amazon Enhanced Scraper Example")
    print("===============================\n")
    
    # Initialize the scraper with more conservative settings
    scraper = AmazonScraper(
        use_proxies=True,
        respect_robots=True,
        delay_range=(5, 10)  # More conservative delays
    )
    
    # Enhance with Selenium capabilities
    try:
        print("Attempting to enhance scraper with Selenium...")
        scraper = extend_with_selenium(scraper, headless=True)
        print("Selenium enhancement successful!")
    except Exception as e:
        print(f"Could not initialize Selenium: {e}")
        print("Continuing with standard scraper.")
    
    # Get search query from user
    search_query = input("\nEnter product search query: ")
    max_pages = int(input("Maximum number of pages to scrape (1-5): ") or "1")
    max_products = int(input("Maximum number of products to scrape (default 3): ") or "3") or 3
    
    print(f"\nSearching for '{search_query}', max {max_pages} pages, max {max_products} products...")
    
    # Scrape products
    try:
        products = scraper.scrape_products(search_query, max_pages, max_products)
        
        if products:
            print(f"\nSuccessfully scraped {len(products)} products!")
            for i, product in enumerate(products):
                print(f"\nProduct {i+1}:")
                print(f"  Title: {product.get('title', 'Unknown')}")
                print(f"  Price: {product.get('price', 'Unknown')}")
                print(f"  Rating: {product.get('rating', 'Unknown')}")
                print(f"  URL: {product.get('url', 'Unknown')}")
        else:
            print("No products found. Try adjusting search terms or scraper settings.")
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        # Ensure proper cleanup
        if hasattr(scraper, 'close'):
            scraper.close()

if __name__ == "__main__":
    main()
```
