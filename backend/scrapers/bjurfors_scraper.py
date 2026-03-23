"""
Scraper for Bjurfors (bjurfors.se)
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
from .base_scraper import BaseRealtorScraper


class BjurforsScraper(BaseRealtorScraper):
    """Scraper for Bjurfors listings"""
    
    REALTOR_NAME = "Bjurfors"
    BASE_URL = "https://www.bjurfors.se"
    # Inner Stockholm - filter lägenhet
    STOCKHOLM_SEARCH_URL = "https://www.bjurfors.se/sv/tillsalu/stockholm/?propertyTypes=lagenhet"
    
    def scrape_listings(self, max_results=50, download_images=True):
        """Scrape Stockholm listings from Bjurfors"""
        driver = self._get_driver()
        listings = []
        
        try:
            print(f"🏠 Scraping {self.REALTOR_NAME}...")
            print(f"   URL: {self.STOCKHOLM_SEARCH_URL}")
            
            driver.get(self.STOCKHOLM_SEARCH_URL)
            time.sleep(4)
            
            # Accept cookies
            self._accept_cookies(driver)
            time.sleep(2)
            
            # Scroll to load more
            print("   Loading listings...")
            for _ in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find listing links - Bjurfors uses /sv/tillsalu/[region]/[area]/[address]/ pattern
            listing_links = soup.select('a[href*="/sv/tillsalu/"]')
            
            # Filter to actual property pages (have address pattern)
            unique_urls = {}
            for link in listing_links:
                href = link.get('href', '')
                # Property URLs have multiple path segments after /tillsalu/
                parts = href.split('/sv/tillsalu/')
                if len(parts) > 1:
                    path = parts[1].strip('/')
                    segments = [s for s in path.split('/') if s]
                    # Real listings have at least 3 segments: region/area/address
                    if len(segments) >= 3:
                        listing_id = segments[-1]  # Use address slug as ID
                        if listing_id not in unique_urls:
                            full_url = href if href.startswith('http') else self.BASE_URL + href
                            unique_urls[listing_id] = full_url
            
            print(f"   Found {len(unique_urls)} unique listings")
            
            urls_to_scrape = list(unique_urls.items())[:max_results]
            
            scraped_count = 0
            for i, (listing_id, url) in enumerate(urls_to_scrape):
                if scraped_count >= max_results:
                    break
                    
                print(f"   [{scraped_count+1}/{max_results}] Scraping {listing_id[:30]}...")
                
                listing_data = self._scrape_listing_details(driver, url, listing_id)
                
                if listing_data:
                    # Filter: only inner Stockholm apartments
                    if not self._is_inner_stockholm(listing_data.get('address'), listing_data.get('area')):
                        print(f"      Skipping: not inner Stockholm")
                        continue
                    if not self._is_apartment(listing_data.get('property_type'), listing_data.get('address', '')):
                        print(f"      Skipping: not apartment")
                        continue
                    
                    if download_images and listing_data.get('image_urls'):
                        print(f"      Downloading {len(listing_data['image_urls'])} images...")
                        local_paths = self._download_images(
                            f"bj_{listing_id[:20]}",
                            listing_data['image_urls']
                        )
                        listing_data['local_image_paths'] = local_paths
                    
                    listings.append(listing_data)
                    scraped_count += 1
                
                time.sleep(1.5)
            
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
        """Scrape full details from a Bjurfors listing page"""
        try:
            driver.get(url)
            time.sleep(3)
            
            self._accept_cookies(driver)
            time.sleep(1)
            
            # Scroll to load images
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            listing = self.get_listing_schema()
            listing['source_id'] = listing_id
            listing['url'] = url
            listing['agency_name'] = self.REALTOR_NAME
            
            # Try JSON-LD first
            json_ld_scripts = soup.select('script[type="application/ld+json"]')
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    
                    types = data.get('@type', [])
                    if isinstance(types, str):
                        types = [types]
                    
                    if any(t in ['RealEstateListing', 'Residence', 'Apartment', 'House', 'Product'] for t in types):
                        listing['raw_data'] = data
                        listing['address'] = data.get('name', '')
                        listing['description'] = data.get('description', '')
                        
                        # Price
                        offers = data.get('offers', {})
                        if isinstance(offers, dict):
                            listing['asking_price'] = self._clean_price(str(offers.get('price', '')))
                        
                        # Images
                        images = data.get('image', [])
                        if isinstance(images, str):
                            images = [images]
                        listing['image_urls'] = [img for img in images if isinstance(img, str)]
                        
                        break
                except:
                    continue
            
            # Parse HTML for additional/fallback data
            if not listing['address']:
                h1 = soup.select_one('h1')
                if h1:
                    text = h1.get_text(strip=True)
                    if 'cookie' not in text.lower() and len(text) > 3:
                        listing['address'] = text
            
            # Extract from URL if no address
            if not listing['address']:
                parts = url.split('/')
                if len(parts) >= 2:
                    listing['address'] = parts[-2].replace('-', ' ').title()
            
            # Price from page
            if not listing['asking_price']:
                price_patterns = soup.select('[class*="price"], [class*="Price"]')
                for elem in price_patterns:
                    text = elem.get_text(strip=True)
                    if 'kr' in text.lower() and any(c.isdigit() for c in text):
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
            
            # Images from page
            if len(listing.get('image_urls', [])) < 5:
                img_elements = soup.select('img[src*="images"], img[src*="cdn"], img[src*="media"], [data-src]')
                for img in img_elements:
                    src = img.get('src') or img.get('data-src')
                    if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = self.BASE_URL + src
                        if src not in listing.get('image_urls', []):
                            listing.setdefault('image_urls', []).append(src)
                
                listing['image_urls'] = listing.get('image_urls', [])[:25]
            
            return listing
            
        except Exception as e:
            print(f"      Error scraping {url}: {e}")
            return None
