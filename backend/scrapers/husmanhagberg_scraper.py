"""
Scraper for HusmanHagberg (husmanhagberg.se)
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import time
import json
import re
from .base_scraper import BaseRealtorScraper


class HusmanHagbergScraper(BaseRealtorScraper):
    """Scraper for HusmanHagberg listings"""
    
    REALTOR_NAME = "HusmanHagberg"
    BASE_URL = "https://www.husmanhagberg.se"
    # Stockholm apartments
    STOCKHOLM_SEARCH_URL = "https://www.husmanhagberg.se/kopa/?l=stockholm&et=Apartment"
    
    def scrape_listings(self, max_results=50, download_images=True):
        """Scrape Stockholm listings from HusmanHagberg"""
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
                
                # Try to click "load more" if present
                try:
                    load_more = driver.find_element(By.XPATH, "//button[contains(text(), 'Visa fler')]")
                    if load_more:
                        load_more.click()
                        time.sleep(2)
                except:
                    pass
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find listing links - HusmanHagberg uses /objekt/[slug]/[ID] pattern
            listing_links = soup.select('a[href*="/objekt/"]')
            
            # Get unique URLs
            unique_urls = {}
            for link in listing_links:
                href = link.get('href', '')
                # Extract ID (last part of URL)
                match = re.search(r'/objekt/[^/]+/(OBJ[A-Z0-9_]+)', href)
                if match:
                    listing_id = match.group(1)
                    if listing_id not in unique_urls:
                        full_url = href if href.startswith('http') else self.BASE_URL + href
                        unique_urls[listing_id] = full_url
            
            print(f"   Found {len(unique_urls)} unique listings")
            
            urls_to_scrape = list(unique_urls.items())[:max_results]
            
            scraped_count = 0
            for i, (listing_id, url) in enumerate(urls_to_scrape):
                if scraped_count >= max_results:
                    break
                    
                print(f"   [{scraped_count+1}/{max_results}] Scraping {listing_id[:20]}...")
                
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
                            f"hh_{listing_id[:15]}",
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
        """Scrape full details from a HusmanHagberg listing page"""
        try:
            driver.get(url)
            time.sleep(3)
            
            self._accept_cookies(driver)
            time.sleep(1)
            
            # Scroll to load content
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            listing = self.get_listing_schema()
            listing['source_id'] = listing_id
            listing['url'] = url
            listing['agency_name'] = self.REALTOR_NAME
            
            # Try JSON-LD
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
                        
                        offers = data.get('offers', {})
                        if isinstance(offers, dict):
                            listing['asking_price'] = self._clean_price(str(offers.get('price', '')))
                        
                        images = data.get('image', [])
                        if isinstance(images, str):
                            images = [images]
                        listing['image_urls'] = [img for img in images if isinstance(img, str)]
                        
                        # Address details
                        addr = data.get('address', {})
                        if isinstance(addr, dict):
                            listing['area'] = addr.get('addressLocality', '')
                        
                        break
                except:
                    continue
            
            # Parse HTML fallbacks
            if not listing['address']:
                h1 = soup.select_one('h1')
                if h1:
                    text = h1.get_text(strip=True)
                    if 'cookie' not in text.lower():
                        listing['address'] = text
            
            # Extract address from URL
            if not listing['address']:
                match = re.search(r'/objekt/([^/]+)/', url)
                if match:
                    listing['address'] = match.group(1).replace('-', ' ').title()
            
            # Price
            if not listing['asking_price']:
                price_elems = soup.select('[class*="price"], [class*="Price"]')
                for elem in price_elems:
                    text = elem.get_text(strip=True)
                    if 'kr' in text.lower():
                        listing['asking_price'] = self._clean_price(text)
                        break
            
            # Page text extraction
            text = soup.get_text()
            
            if not listing['size_sqm']:
                size_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(?:m²|kvm|m2)', text, re.I)
                if size_match:
                    listing['size_sqm'] = self._clean_size(size_match.group(1))
            
            if not listing['rooms']:
                rooms_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*rum', text, re.I)
                if rooms_match:
                    listing['rooms'] = self._clean_rooms(rooms_match.group(1))
            
            if not listing['monthly_fee']:
                fee_match = re.search(r'avgift[:\s]*(\d[\d\s]*)\s*kr', text, re.I)
                if fee_match:
                    listing['monthly_fee'] = self._clean_price(fee_match.group(1))
            
            # Images from page
            if len(listing.get('image_urls', [])) < 5:
                img_elements = soup.select('img[src*="images"], img[src*="cdn"], img[src*="media"], img[data-src], picture source')
                for img in img_elements:
                    src = img.get('src') or img.get('srcset', '').split()[0] or img.get('data-src')
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
