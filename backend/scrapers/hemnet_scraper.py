import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
from urllib.parse import urlencode, quote
from storage.database import HemnetDatabase
from storage.image_manager import ImageManager


class HemnetScraper:
    """Scraper for Hemnet.se active listings"""

    def __init__(self):
        self.base_url = "https://www.hemnet.se"
        self.db = HemnetDatabase()
        self.image_manager = ImageManager()

    def _get_driver(self):
        """Initialize Selenium WebDriver (headless Chrome)"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Use a realistic user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Add language preferences
        chrome_options.add_argument("--lang=sv-SE")
        chrome_options.add_argument("--accept-lang=sv-SE,sv;q=0.9,en;q=0.8")

        driver = webdriver.Chrome(options=chrome_options)

        # Execute CDP commands to hide webdriver property
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def scrape_for_sale(self, location_ids=['925970'], property_type='lägenhet',
                       min_price=None, max_price=None, min_rooms=None, max_rooms=None,
                       min_size=None, max_size=None, max_results=10, download_images=True):
        """
        Scrape active "Till Salu" listings from Hemnet

        Args:
            location_ids: List of Hemnet location IDs (17744 = Vasastan, Stockholm)
            property_type: Type of property (lägenhet, villa, etc.)
            min_price: Minimum asking price
            max_price: Maximum asking price
            min_rooms: Minimum number of rooms
            max_rooms: Maximum number of rooms
            min_size: Minimum size in m²
            max_size: Maximum size in m²
            max_results: Maximum number of listings to scrape
            download_images: Whether to download images (default: True)

        Returns:
            List of listing dictionaries
        """
        # Build search URL
        # Note: We need to manually build the URL because Hemnet requires location_ids[]
        # (empty brackets) which urlencode doesn't handle well
        params = []

        # Location IDs - use empty brackets as Hemnet expects
        for loc_id in location_ids:
            params.append(f'location_ids[]={loc_id}')

        # Property type
        if property_type.lower() == 'lägenhet':
            params.append('item_types[]=bostadsratt')
        elif property_type.lower() == 'villa':
            params.append('item_types[]=villa')
        elif property_type.lower() == 'radhus':
            params.append('item_types[]=radhus')

        # Price range
        if min_price:
            params.append(f'price_min={min_price}')
        if max_price:
            params.append(f'price_max={max_price}')

        # Rooms
        if min_rooms:
            params.append(f'rooms_min={min_rooms}')
        if max_rooms:
            params.append(f'rooms_max={max_rooms}')

        # Size
        if min_size:
            params.append(f'living_area_min={min_size}')
        if max_size:
            params.append(f'living_area_max={max_size}')

        # Build the final URL
        search_url = f"{self.base_url}/bostader?{'&'.join(params)}"

        driver = self._get_driver()
        listings = []

        try:
            print(f"Fetching Hemnet: {search_url}")
            driver.get(search_url)

            # Handle cookie consent if present
            try:
                time.sleep(2)
                # Try to find and accept cookies
                accept_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Godkänn') or contains(text(), 'Acceptera')]")
                if accept_buttons:
                    print("Accepting cookies...")
                    accept_buttons[0].click()
                    time.sleep(1)
            except Exception as e:
                print(f"No cookie banner or already accepted: {e}")

            # Wait for listings to load - try multiple selectors
            print("Waiting for listings to load...")
            selectors_to_try = [
                'a[href*="/bostad/"]',  # Most reliable - links to properties
                'article',
                'li[data-test]',
                '.property-card',
                '[class*="PropertyCard"]',
                '[class*="ListingCard"]',
            ]

            page_loaded = False
            for selector in selectors_to_try:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Page loaded! Found elements with selector: {selector}")
                    page_loaded = True
                    break
                except:
                    continue

            if not page_loaded:
                print("Warning: Could not find listings with standard selectors")
                print("Saving page source for debugging...")
                with open('hemnet_debug.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("Page source saved to hemnet_debug.html")

            # Give extra time for dynamic content
            time.sleep(5)

            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract data from __NEXT_DATA__ JSON (Hemnet uses Apollo GraphQL)
            print("Extracting listing data from __APOLLO_STATE__...")
            unique_listings = {}

            try:
                # Find the __NEXT_DATA__ script tag
                next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
                if next_data_script:
                    next_data = json.loads(next_data_script.string)

                    # Get Apollo state (similar to Booli)
                    apollo_state = next_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

                    if apollo_state:
                        # Get ROOT_QUERY which contains the actual search results
                        root_query = apollo_state.get('ROOT_QUERY', {})

                        # Find the searchForSaleListings field that matches our search
                        # Look for the one with offset:0 (first page) and highest limit
                        search_results = None
                        best_limit = 0
                        for key, value in root_query.items():
                            if 'searchForSaleListings' in key and '"offset":0' in key:
                                # Extract limit from key
                                limit_match = re.search(r'"limit":(\d+)', key)
                                if limit_match:
                                    limit_val = int(limit_match.group(1))
                                    if limit_val > best_limit:
                                        best_limit = limit_val
                                        search_results = value

                        if search_results and 'cards' in search_results:
                            # Extract listing IDs from the cards array
                            cards = search_results.get('cards', [])
                            print(f"Found {len(cards)} listings in search results")

                            for card_ref in cards:
                                # card_ref looks like {"__ref": "ListingCard:21630953"}
                                ref = card_ref.get('__ref', '')
                                if ref.startswith('ListingCard:'):
                                    listing_id = ref.replace('ListingCard:', '')
                                    url = f"{self.base_url}/bostad/{listing_id}"

                                    # Extract data from the ListingCard in Apollo state
                                    listing_card = apollo_state.get(ref, {})

                                    # Parse the data from ListingCard
                                    listing_data = {
                                        'url': url,
                                        'hemnet_id': str(listing_id)
                                    }

                                    # Extract asking price (e.g., "7 850 000 kr" -> 7850000)
                                    # Note: Hemnet uses non-breaking spaces (\xa0) not regular spaces
                                    asking_price_str = listing_card.get('askingPrice', '')
                                    if asking_price_str:
                                        price_match = re.search(r'([\d\s\xa0]+)', asking_price_str)
                                        if price_match:
                                            try:
                                                # Remove both regular spaces and non-breaking spaces
                                                cleaned_price = price_match.group(1).replace(' ', '').replace('\xa0', '')
                                                listing_data['asking_price'] = int(cleaned_price)
                                            except:
                                                pass

                                    # Extract monthly fee (e.g., "3 317 kr/mån" -> 3317)
                                    # Note: Hemnet uses non-breaking spaces (\xa0) not regular spaces
                                    fee_str = listing_card.get('fee', '')
                                    if fee_str:
                                        fee_match = re.search(r'([\d\s\xa0]+)', fee_str)
                                        if fee_match:
                                            try:
                                                # Remove both regular spaces and non-breaking spaces
                                                cleaned_fee = fee_match.group(1).replace(' ', '').replace('\xa0', '')
                                                listing_data['monthly_fee'] = int(cleaned_fee)
                                            except:
                                                pass

                                    # Extract rooms (e.g., "2 rum" -> 2.0)
                                    rooms_str = listing_card.get('rooms', '')
                                    if rooms_str:
                                        rooms_match = re.search(r'([\d,\.]+)', rooms_str)
                                        if rooms_match:
                                            try:
                                                listing_data['rooms'] = float(rooms_match.group(1).replace(',', '.'))
                                            except:
                                                pass

                                    # Extract floor (e.g., "vån 2" -> "2")
                                    floor_str = listing_card.get('floor', '')
                                    if floor_str:
                                        listing_data['floor'] = floor_str

                                    # Extract address
                                    street_address = listing_card.get('streetAddress', '')
                                    if street_address:
                                        listing_data['address'] = street_address

                                    # Extract living area (e.g., from livingAndSupplementalAreas "59 m²")
                                    living_area = listing_card.get('livingAndSupplementalAreas', '')
                                    if living_area:
                                        # Try to extract m² value
                                        area_match = re.search(r'([\d,\.]+)\s*m', living_area)
                                        if area_match:
                                            try:
                                                listing_data['size_sqm'] = float(area_match.group(1).replace(',', '.'))
                                            except:
                                                pass

                                    # Extract broker/agent name
                                    broker_name = listing_card.get('brokerName', '')
                                    if broker_name:
                                        listing_data['agent_name'] = broker_name

                                    # Extract broker agency name
                                    agency_name = listing_card.get('brokerAgencyName', '')
                                    if agency_name:
                                        listing_data['agency_name'] = agency_name

                                    unique_listings[url] = listing_data
                        else:
                            print("⚠️  Could not find searchForSaleListings in ROOT_QUERY")
                            print(f"Available ROOT_QUERY keys: {list(root_query.keys())[:5]}")

                        print(f"Extracted {len(unique_listings)} unique listings from search results")

                        # Debug: Save the __NEXT_DATA__ for inspection
                        with open('hemnet_next_data.json', 'w', encoding='utf-8') as f:
                            json.dump(next_data, f, indent=2, ensure_ascii=False)

                    else:
                        print("⚠️  No __APOLLO_STATE__ found in __NEXT_DATA__")
                else:
                    print("❌ No __NEXT_DATA__ found")

            except Exception as e:
                print(f"Error extracting data: {e}")
                import traceback
                traceback.print_exc()

            print(f"Total unique listings found: {len(unique_listings)}")

            # Determine how many to scrape
            if max_results == 'all':
                limit = len(unique_listings)
            else:
                try:
                    limit = min(int(max_results), len(unique_listings))
                except ValueError:
                    limit = min(10, len(unique_listings))

            print(f"Scraping {limit} listings...")

            # Scrape each listing
            for idx, (url, listing_info) in enumerate(list(unique_listings.items())[:limit]):
                print(f"\n[{idx + 1}/{limit}] Scraping: {url}")
                listing_data = self._scrape_listing_details(driver, url, listing_info)

                if listing_data:
                    # Save to database
                    listing_id = self.db.insert_listing(listing_data)

                    # Save image URLs to database
                    if 'image_urls' in listing_data and listing_data['image_urls']:
                        self.db.insert_images(listing_id, listing_data['image_urls'])

                        # Download images if requested
                        if download_images:
                            local_paths = self.image_manager.download_all_images(
                                listing_data['hemnet_id'],
                                listing_data['image_urls']
                            )

                    listings.append(listing_data)

                time.sleep(2)  # Be polite

        finally:
            driver.quit()

        print(f"\n✅ Scraped and saved {len(listings)} listings to database")
        return listings

    def _scrape_listing_details(self, driver, url, listing_info):
        """
        Scrape additional details from an individual listing page.
        The listing_info already contains data extracted from Apollo state.

        Args:
            driver: Selenium WebDriver instance
            url: URL of the listing
            listing_info: Dictionary with pre-extracted data from Apollo state

        Returns:
            Dictionary with complete listing details
        """
        try:
            driver.get(url)
            time.sleep(3)

            # Scroll to load all images
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Start with pre-extracted data from Apollo state
            listing = {
                **listing_info,  # Includes: hemnet_id, url, asking_price, monthly_fee, rooms, floor, address, size_sqm
                'status': 'active',
                'image_urls': []
            }

            # Print the pre-extracted data
            if 'asking_price' in listing:
                print(f"  Asking Price (from Apollo): {listing['asking_price']} SEK")
            if 'monthly_fee' in listing:
                print(f"  Monthly Fee (from Apollo): {listing['monthly_fee']} SEK")
            if 'rooms' in listing:
                print(f"  Rooms (from Apollo): {listing['rooms']}")
            if 'size_sqm' in listing:
                print(f"  Size (from Apollo): {listing['size_sqm']} m²")
            if 'floor' in listing:
                print(f"  Floor (from Apollo): {listing['floor']}")
            if 'address' in listing:
                print(f"  Address (from Apollo): {listing['address']}")

            # Extract agent/agency info
            agent_elem = soup.select_one('.broker__name, [class*="broker-name"], .property-broker__name')
            if agent_elem:
                listing['agent_name'] = agent_elem.get_text(strip=True)
                print(f"  Agent: {listing['agent_name']}")

            agency_elem = soup.select_one('.broker__agency, [class*="broker-firm"], .property-broker__firm')
            if agency_elem:
                listing['agency_name'] = agency_elem.get_text(strip=True)
                print(f"  Agency: {listing['agency_name']}")

            # Extract description
            desc_elem = soup.select_one('.property-description, [class*="description"]')
            if desc_elem:
                listing['description'] = desc_elem.get_text(strip=True)[:1000]  # Limit length

            # Extract images
            # Hemnet uses various image containers
            image_elems = soup.select('img[src*="hemnet"], picture source[srcset*="hemnet"], .image-gallery img')

            image_urls = set()
            for img in image_elems:
                # Try to get highest quality image URL
                img_url = None

                # Check srcset first (usually has higher quality)
                srcset = img.get('srcset')
                if srcset:
                    # Parse srcset and get largest image
                    srcset_urls = re.findall(r'(https?://[^\s]+)', srcset)
                    if srcset_urls:
                        img_url = srcset_urls[-1]  # Usually last is largest

                # Fallback to src
                if not img_url:
                    img_url = img.get('src')

                # Clean up URL and add if valid
                if img_url and 'hemnet' in img_url and '/images/' in img_url:
                    # Remove query params for deduplication
                    img_url = img_url.split('?')[0]
                    image_urls.add(img_url)

            listing['image_urls'] = list(image_urls)
            print(f"  Found {len(listing['image_urls'])} images")

            return listing

        except Exception as e:
            print(f"  Error scraping listing: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_saved_listings(self, status='active', limit=None):
        """Get saved listings from database"""
        return self.db.get_listings(status=status, limit=limit)

    def get_database_stats(self):
        """Get database statistics"""
        db_stats = self.db.get_stats()
        storage_stats = self.image_manager.get_storage_stats()

        return {
            **db_stats,
            **storage_stats
        }
