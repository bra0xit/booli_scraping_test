"""
Scraper for Svensk Fastighetsförmedling (svenskfast.se)
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
from .base_scraper import BaseRealtorScraper


class SvenskfastScraper(BaseRealtorScraper):
    """Scraper for Svensk Fastighetsförmedling listings"""
    
    REALTOR_NAME = "Svensk Fastighetsförmedling"
    BASE_URL = "https://www.svenskfast.se"
    # Filter: Stockholm inner city, apartments
    STOCKHOLM_SEARCH_URL = "https://www.svenskfast.se/bostad/?location=stockholm&propertyType=apartment"
    
    def scrape_listings(self, max_results=50, download_images=True):
        """
        Scrape Stockholm listings from Svensk Fastighetsförmedling
        Uses JSON-LD data embedded in search results page
        """
        driver = self._get_driver()
        listings = []
        
        try:
            print(f"🏠 Scraping {self.REALTOR_NAME}...")
            print(f"   URL: {self.STOCKHOLM_SEARCH_URL}")
            
            driver.get(self.STOCKHOLM_SEARCH_URL)
            time.sleep(4)
            
            # Accept cookies
            try:
                from selenium.webdriver.common.by import By
                btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
                btn.click()
                time.sleep(2)
            except:
                pass
            
            # Scroll to load more
            print("   Loading listings...")
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract listings from JSON-LD (Svenskfast embeds full listing data)
            json_ld_scripts = soup.select('script[type="application/ld+json"]')
            print(f"   Found {len(json_ld_scripts)} JSON-LD scripts")
            
            listing_count = 0
            for script in json_ld_scripts:
                if listing_count >= max_results:
                    break
                    
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    
                    # Check if it's a RealEstateListing
                    listing_type = data.get('@type', '')
                    if listing_type != 'RealEstateListing':
                        continue
                    
                    listing = self.get_listing_schema()
                    listing['raw_data'] = data
                    
                    # Extract URL and ID
                    url = data.get('url', '')
                    listing['url'] = url
                    
                    # Extract ID from URL
                    match = re.search(r'/(\d+)/?$', url)
                    if match:
                        listing['source_id'] = match.group(1)
                    else:
                        listing['source_id'] = str(hash(url))[:10]
                    
                    # Name/Address
                    listing['address'] = data.get('name', '')
                    
                    # Description
                    listing['description'] = data.get('description', '')
                    
                    # Price
                    offers = data.get('offers', {})
                    if isinstance(offers, dict):
                        price = offers.get('price')
                        if price:
                            listing['asking_price'] = int(price) if isinstance(price, (int, float)) else self._clean_price(str(price))
                    
                    # Images
                    images = data.get('image', [])
                    if isinstance(images, str):
                        images = [images]
                    elif isinstance(images, dict):
                        images = [images.get('url', '')]
                    listing['image_urls'] = [img for img in images if img and isinstance(img, str)]
                    
                    # Address details
                    address_data = data.get('address', {})
                    if isinstance(address_data, dict):
                        listing['area'] = address_data.get('addressLocality', '')
                    
                    # Floor size
                    floor_size = data.get('floorSize', {})
                    if isinstance(floor_size, dict):
                        listing['size_sqm'] = floor_size.get('value')
                    
                    # Rooms
                    listing['rooms'] = data.get('numberOfRooms')
                    
                    # Filter: only inner Stockholm apartments
                    if not self._is_inner_stockholm(listing.get('address'), listing.get('area')):
                        continue
                    if not self._is_apartment(listing.get('property_type'), listing.get('address', '')):
                        continue
                    
                    # Download images if requested
                    if download_images and listing.get('image_urls'):
                        print(f"   [{listing_count+1}] {listing['address'][:40]}... ({len(listing['image_urls'])} images)")
                        local_paths = self._download_images(
                            f"sf_{listing['source_id']}",
                            listing['image_urls']
                        )
                        listing['local_image_paths'] = local_paths
                    else:
                        print(f"   [{listing_count+1}] {listing['address'][:40]}...")
                    
                    listings.append(listing)
                    listing_count += 1
                    
                except Exception as e:
                    continue
            
            print(f"✅ Scraped {len(listings)} listings from {self.REALTOR_NAME}")
            
        except Exception as e:
            print(f"❌ Error scraping {self.REALTOR_NAME}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()
        
        return listings
    
    def _parse_listing_card(self, card_element):
        pass
    
    def _scrape_listing_details(self, driver, url, listing_id):
        """Scrape full details from a listing page"""
        try:
            driver.get(url)
            time.sleep(3)
            
            self._accept_cookies(driver)
            time.sleep(1)
            
            # Scroll to load images
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            listing = self.get_listing_schema()
            listing['source_id'] = listing_id
            listing['url'] = url
            
            # Extract from JSON-LD
            json_ld_scripts = soup.select('script[type="application/ld+json"]')
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    
                    types = data.get('@type', [])
                    if isinstance(types, str):
                        types = [types]
                    
                    # Look for Product or RealEstateListing
                    if any(t in types for t in ['Product', 'RealEstateListing', 'Apartment', 'House', 'Residence']):
                        listing['raw_data'] = data
                        
                        listing['address'] = data.get('name') or data.get('address', {}).get('streetAddress')
                        listing['description'] = data.get('description')
                        
                        # Price from offers
                        offers = data.get('offers', {})
                        if isinstance(offers, dict):
                            listing['asking_price'] = self._clean_price(str(offers.get('price', '')))
                        
                        # Images
                        images = data.get('image', [])
                        if isinstance(images, str):
                            images = [images]
                        listing['image_urls'] = [img for img in images if isinstance(img, str)]
                        
                        break
                        
                except Exception as e:
                    continue
            
            # Parse HTML for additional details
            # Address
            if not listing['address']:
                h1 = soup.select_one('h1')
                if h1:
                    text = h1.get_text(strip=True)
                    if 'cookie' not in text.lower():
                        listing['address'] = text
            
            # Price
            if not listing['asking_price']:
                price_elems = soup.select('[class*="price"], [class*="Price"]')
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    if 'kr' in text.lower():
                        listing['asking_price'] = self._clean_price(text)
                        break
            
            # Size and rooms from page text
            text = soup.get_text()
            
            if not listing['size_sqm']:
                size_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(?:m²|kvm|m2)', text, re.I)
                if size_match:
                    listing['size_sqm'] = self._clean_size(size_match.group(1))
            
            if not listing['rooms']:
                rooms_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*rum', text, re.I)
                if rooms_match:
                    listing['rooms'] = self._clean_rooms(rooms_match.group(1))
            
            # Monthly fee
            if not listing['monthly_fee']:
                fee_match = re.search(r'avgift[:\s]*(\d[\d\s]*)\s*kr', text, re.I)
                if fee_match:
                    listing['monthly_fee'] = self._clean_price(fee_match.group(1))
            
            # Get more images from page
            if len(listing.get('image_urls', [])) < 5:
                img_elements = soup.select('img[src*="images"], img[src*="cdn"], img[src*="property"], [data-src]')
                for img in img_elements:
                    src = img.get('src') or img.get('data-src')
                    if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = self.BASE_URL + src
                        if src not in listing.get('image_urls', []) and 'svenskfast' in src:
                            listing.setdefault('image_urls', []).append(src)
                
                listing['image_urls'] = listing.get('image_urls', [])[:25]
            
            return listing
            
        except Exception as e:
            print(f"      Error scraping {url}: {e}")
            return None
