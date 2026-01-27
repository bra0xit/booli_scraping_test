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
from storage.database import BooliDatabase


class BooliScraper:
    """Scraper for Booli.se sold apartments"""

    def __init__(self):
        self.base_url = "https://www.booli.se"
        self.agent_mapping = self._load_mapping()
        self.db = BooliDatabase()

    def _load_mapping(self):
        """Load agent and agency name mappings from JSON file"""
        mapping_file = os.path.join(os.path.dirname(__file__), '..', 'agent_agency_mapping.json')
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load agent mapping file: {e}")
            return {"agents": {}, "agencies": {}}

    def _get_driver(self):
        """Initialize Selenium WebDriver (headless Chrome)"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Hide automation
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Use a realistic user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Add language preferences
        chrome_options.add_argument("--lang=sv-SE")
        chrome_options.add_argument("--accept-lang=sv-SE,sv;q=0.9,en;q=0.8")

        # Disable webdriver flag
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(options=chrome_options)

        # Execute CDP commands to hide webdriver property
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def scrape_sold_apartments(self, area_id='115349', object_type='Lägenhet',
                               min_price='8000000', max_price='10000000',
                               min_rooms='', max_rooms='', min_area='', max_area='',
                               max_results='10'):
        """
        Scrape sold apartments from Booli.se

        Args:
            area_id: Area ID for the search
            object_type: Type of property (Lägenhet, Villa, etc.)
            min_price: Minimum sold price
            max_price: Maximum sold price
            min_rooms: Minimum number of rooms
            max_rooms: Maximum number of rooms
            min_area: Minimum living area in m²
            max_area: Maximum living area in m²
            max_results: Maximum number of results to return

        Returns:
            List of apartment dictionaries
        """
        # URL encode the object type
        import urllib.parse
        object_type_encoded = urllib.parse.quote(object_type)

        # Build the search URL with all parameters
        search_url = f"{self.base_url}/sok/slutpriser?areaIds={area_id}&objectType={object_type_encoded}&minSoldPrice={min_price}&maxSoldPrice={max_price}"

        # Add optional parameters if provided
        if min_rooms:
            search_url += f"&minRooms={min_rooms}"
        if max_rooms:
            search_url += f"&maxRooms={max_rooms}"
        if min_area:
            search_url += f"&minLivingArea={min_area}"
        if max_area:
            search_url += f"&maxLivingArea={max_area}"

        driver = self._get_driver()
        apartments = []

        try:
            print(f"Fetching: {search_url}")
            driver.get(search_url)

            # Handle cookie consent if present
            try:
                time.sleep(2)  # Wait for cookie banner to appear
                # Try to find and click "Godkänn" (Accept) button for cookies
                accept_button = driver.find_element(By.ID, "didomi-notice-agree-button")
                if accept_button:
                    print("Accepting cookies...")
                    accept_button.click()
                    time.sleep(1)
            except Exception as e:
                print(f"No cookie banner or already accepted: {e}")

            # Wait for listings to load - Booli uses article.relative for each listing
            print("Waiting for listings to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.relative"))
            )

            # Give it a bit more time for dynamic content
            time.sleep(3)
            print("Page loaded successfully!")

            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find all listing links - they use class "expanded-link" with href containing /annons/ or /bostad/
            listing_elements = soup.select('a.expanded-link[href*="/annons/"], a.expanded-link[href*="/bostad/"]')

            # Remove duplicates by using href as key
            unique_listings = {}
            for link in listing_elements:
                href = link.get('href')
                if href and href not in unique_listings:
                    unique_listings[href] = link

            listing_elements = list(unique_listings.values())

            print(f"Found {len(listing_elements)} listings")

            # Determine how many results to scrape
            if max_results == 'all':
                limit = len(listing_elements)
            else:
                try:
                    limit = min(int(max_results), len(listing_elements))
                except ValueError:
                    limit = min(10, len(listing_elements))

            print(f"Scraping {limit} apartments...")

            for listing in listing_elements[:limit]:
                listing_url = listing.get('href')
                if not listing_url.startswith('http'):
                    listing_url = self.base_url + listing_url

                print(f"Scraping: {listing_url}")
                apartment_data = self._scrape_apartment_details(driver, listing_url)

                if apartment_data:
                    # Save to database (will prevent duplicates)
                    apartment_id = self.db.insert_apartment(apartment_data)
                    apartment_data['db_id'] = apartment_id
                    apartments.append(apartment_data)

                time.sleep(1)  # Be polite, don't hammer the server

        finally:
            driver.quit()

        print(f"\n✅ Scraped and saved {len(apartments)} apartments to database")
        return apartments

    def _scrape_apartment_details(self, driver, url):
        """
        Scrape details from an individual apartment listing

        Args:
            driver: Selenium WebDriver instance
            url: URL of the apartment listing

        Returns:
            Dictionary with apartment details
        """
        try:
            driver.get(url)

            # Wait longer for dynamic content to load
            time.sleep(3)

            # Scroll down to trigger lazy loading of agent/agency information
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Scroll back up
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # These selectors are placeholders and need to be adjusted
            # based on actual Booli.se HTML structure
            apartment = {
                'url': url,
                'address': None,
                'agent': None,
                'agent_url': None,
                'agency': None,
                'agency_url': None,
                'sold_price': None,
                'sold_date': None,
            }

            # Find address - usually in h1 tag on detail pages
            address_elem = soup.select_one('h1')
            if address_elem:
                apartment['address'] = address_elem.get_text(strip=True)

            # Find sold price - look for price with "kr" or price-related class
            price_elem = soup.select_one('.object-card__price__logo, [class*="price"]')
            if price_elem:
                apartment['sold_price'] = price_elem.get_text(strip=True)

            # Try alternate method for price
            if not apartment['sold_price']:
                price_text = soup.find(string=lambda x: x and 'kr' in str(x) and any(c.isdigit() for c in str(x)))
                if price_text:
                    apartment['sold_price'] = price_text.strip()

            # Find sold date
            date_elem = soup.select_one('.object-card__date__logo, [class*="date"]')
            if date_elem:
                apartment['sold_date'] = date_elem.get_text(strip=True)

            # Extract agent and agency from JSON data in page
            try:
                # Find the __NEXT_DATA__ script tag which contains all page data
                script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
                if script_tag:
                    json_data = json.loads(script_tag.string)
                    apollo_state = json_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

                    # Find the SoldProperty entry
                    for key, value in apollo_state.items():
                        if key.startswith('SoldProperty:'):
                            agent_id = value.get('agentId')
                            agency_id = value.get('agencyId')

                            if agent_id:
                                # Look up agent name in mapping
                                agent_name = self.agent_mapping.get('agents', {}).get(str(agent_id))

                                if agent_name:
                                    apartment['agent'] = agent_name
                                    print(f"  Found agent: {agent_name} (ID: {agent_id})")
                                else:
                                    apartment['agent'] = f"Agent ID: {agent_id}"
                                    print(f"  Agent ID {agent_id} not in mapping - add to agent_agency_mapping.json")

                                apartment['agent_url'] = f"https://www.hittamaklare.se/maklare/{agent_id}"

                            if agency_id:
                                # Look up agency name in mapping
                                agency_name = self.agent_mapping.get('agencies', {}).get(str(agency_id))

                                if agency_name:
                                    apartment['agency'] = agency_name
                                    print(f"  Found agency: {agency_name} (ID: {agency_id})")
                                else:
                                    apartment['agency'] = f"Agency ID: {agency_id}"
                                    print(f"  Agency ID {agency_id} not in mapping - add to agent_agency_mapping.json")

                                apartment['agency_url'] = f"https://www.hittamaklare.se/maklarbyra/{agency_id}"

                            break
            except Exception as e:
                print(f"  Could not extract agent/agency from JSON: {e}")

            return apartment

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def get_saved_apartments(self, limit=None):
        """Get saved apartments from database"""
        return self.db.get_apartments(limit=limit)

    def get_database_stats(self):
        """Get database statistics"""
        return self.db.get_stats()
