# Web-Scrapers

A collection of robust, feature-rich web scraping tools designed to extract, analyze, and visualize data from major platforms such as Amazon and Google News. This project aims to provide flexible, ethical, and powerful scrapers for research, data analysis, and trend monitoring.

## Project Structure

- **amazon_scraper/** – Scrapes product data from Amazon with advanced analysis.
- **google_news_scraper/** – Collects and analyzes AI-related news articles from Google News.
- More scrapers can be added in the future.

## Key Features

- **Rate Limiting & Human-like Behavior**: All scrapers implement random delays and optional proxy/user-agent rotation to avoid detection and minimize server impact.
- **Configurable & Modular**: Each scraper is standalone and easy to configure for specific needs.
- **Comprehensive Data Extraction**: Extracts detailed, structured information from target sites, including product details, news metadata, and more.
- **Automated Data Analysis**: Built-in analytics for insights (e.g., top-rated products, price ranges, publisher distributions, keyword clouds).
- **Multiple Output Formats**: Data exported as JSON and CSV for easy use in research and analytics.
- **Visualization**: Where applicable, generates visualizations such as word clouds and timeline charts.
- **Logging & Error Handling**: Sophisticated retry mechanisms and detailed logging for reliability and debugging.
- **Ethical Scraping**: Options to respect robots.txt rules and minimize requests.

## Included Scrapers

### Amazon Product Scraper

- Extracts product titles, prices, ratings, reviews, features, specs, and images.
- Analyzes results for top products, price statistics, rating distributions, and common features.
- Outputs: JSON, CSV, and analysis reports.
- Best practices: Rate limiting, user-agent & proxy rotation, error handling.
- **Disclaimer:** For educational use. Use at your own risk; scraping Amazon may violate their ToS.

### Google News AI Scraper

- Targets AI-related news on Google News.
- Extracts titles, URLs, publishers, times, snippets, and thumbnails.
- Provides analysis: publisher frequency, publication timeline, keyword and topic extraction, visualizations (word cloud, timeline chart).
- Outputs: JSON, CSV, analysis JSON, PNG images (visualizations).
- Ethical scraping practices in place.
- **Disclaimer:** For educational use. Scraping Google News may violate their ToS.

## Setup

Each scraper has its own requirements and setup instructions. See the README in each subdirectory for full details.

**General steps:**
1. Install Python dependencies (see individual scraper folders).
2. Run the appropriate script and follow prompts.
3. View and analyze the generated data and reports.

## Limitations

- Website structures may change, requiring code updates.
- Free proxies can be unreliable.
- CAPTCHAs or anti-bot measures may still occur.
- Analysis is limited by available data and basic NLP techniques.

## Disclaimer

This repository is for educational and research purposes only. Web scraping may violate the terms of service of target sites. Use responsibly and at your own risk.
