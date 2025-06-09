"""
Amazon Scraper Package

A robust and ethical web scraper for Amazon product information,
with features like proxy rotation, robots.txt compliance, 
and multiple extraction methods.
"""

from .amazon_scraper import AmazonScraper

try:
    from .amazon_selenium import AmazonSeleniumExtractor
    
    # Extend the AmazonScraper with Selenium capabilities
    def extend_with_selenium(scraper_instance, headless=True):
        """
        Extend an AmazonScraper instance with Selenium capabilities
        
        Args:
            scraper_instance (AmazonScraper): The scraper to enhance
            headless (bool): Whether to run Chrome in headless mode
            
        Returns:
            AmazonScraper: The enhanced scraper instance
        """
        selenium_extractor = AmazonSeleniumExtractor(headless=headless)
        
        # Add the extract_with_selenium method to the scraper
        scraper_instance.extract_with_selenium = selenium_extractor.extract_with_selenium
        scraper_instance.selenium_extractor = selenium_extractor
        
        # Override the close method to ensure the Selenium driver is closed
        original_close = getattr(scraper_instance, 'close', lambda: None)
        
        def enhanced_close():
            selenium_extractor.close()
            original_close()
        
        scraper_instance.close = enhanced_close
        
        return scraper_instance
        
except ImportError:
    # Selenium not available, provide a dummy function
    def extend_with_selenium(scraper_instance, headless=True):
        print("Selenium enhancement not available. Please install selenium and webdriver_manager.")
        return scraper_instance
```
