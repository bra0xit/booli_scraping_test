"""
Base scraper class for Swedish realtor websites
All realtor scrapers inherit from this class for consistency
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from storage.image_manager import ImageManager


class BaseRealtorScraper(ABC):
    """
    Abstract base class for realtor website scrapers.
    
    Each realtor scraper should implement:
    - scrape_listings(): Main method to scrape all Stockholm listings
    - _parse_listing_card(): Parse a listing from search results
    - _scrape_listing_details(): Scrape full details from listing page
    """
    
    # Override these in subclasses
    REALTOR_NAME = "Base"
    BASE_URL = ""
    STOCKHOLM_SEARCH_URL = ""
    
    def __init__(self, db=None):
        self.image_manager = ImageManager()
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        })
    
    def _get_driver(self):
        """Initialize Selenium WebDriver (headless Chrome)"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--lang=sv-SE")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _accept_cookies(self, driver):
        """Try to accept cookie consent banners"""
        cookie_selectors = [
            "//button[contains(text(), 'Godkänn')]",
            "//button[contains(text(), 'Acceptera')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(@id, 'accept')]",
            "//button[contains(@class, 'accept')]",
            "#didomi-notice-agree-button",
            "#onetrust-accept-btn-handler",
        ]
        
        for selector in cookie_selectors:
            try:
                if selector.startswith("//"):
                    btn = driver.find_element(By.XPATH, selector)
                else:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn:
                    btn.click()
                    print(f"  Accepted cookies via {selector}")
                    time.sleep(1)
                    return True
            except:
                continue
        return False
    
    def _download_images(self, listing_id, image_urls):
        """Download all images for a listing"""
        if not image_urls:
            return []
        
        return self.image_manager.download_all_images(listing_id, image_urls)
    
    def _clean_price(self, price_str):
        """Extract numeric price from string like '5 950 000 kr'"""
        if not price_str:
            return None
        import re
        # Remove everything except digits
        digits = re.sub(r'[^\d]', '', price_str)
        return int(digits) if digits else None
    
    def _clean_size(self, size_str):
        """Extract numeric size from string like '67 m²'"""
        if not size_str:
            return None
        import re
        match = re.search(r'([\d,\.]+)', size_str)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    def _clean_rooms(self, rooms_str):
        """Extract room count from string like '3 rum'"""
        if not rooms_str:
            return None
        import re
        match = re.search(r'([\d,\.]+)', rooms_str)
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    @abstractmethod
    def scrape_listings(self, max_results=50, download_images=True):
        """
        Scrape listings from the realtor website.
        
        Args:
            max_results: Maximum number of listings to scrape
            download_images: Whether to download listing images
            
        Returns:
            List of listing dictionaries
        """
        pass
    
    @abstractmethod
    def _parse_listing_card(self, card_element):
        """
        Parse a listing card from search results.
        
        Args:
            card_element: BeautifulSoup element for the listing card
            
        Returns:
            Dictionary with basic listing info (url, address, price, etc.)
        """
        pass
    
    @abstractmethod
    def _scrape_listing_details(self, driver, listing_url):
        """
        Scrape full details from a listing page.
        
        Args:
            driver: Selenium WebDriver instance
            listing_url: URL of the listing
            
        Returns:
            Dictionary with full listing details including image URLs
        """
        pass
    
    def get_listing_schema(self):
        """Return the standard schema for listings"""
        return {
            'source': self.REALTOR_NAME,
            'source_id': None,  # Unique ID from the realtor
            'url': None,
            'address': None,
            'area': None,  # Neighborhood/area name
            'city': 'Stockholm',
            'asking_price': None,
            'monthly_fee': None,  # Månadsavgift
            'rooms': None,
            'size_sqm': None,
            'floor': None,
            'build_year': None,
            'property_type': None,  # lägenhet, villa, etc.
            'agent_name': None,
            'agent_phone': None,
            'agent_email': None,
            'agency_name': self.REALTOR_NAME,
            'description': None,
            'image_urls': [],
            'local_image_paths': [],
            'scraped_at': datetime.now().isoformat(),
            'raw_data': None,  # Store original data for debugging
        }
