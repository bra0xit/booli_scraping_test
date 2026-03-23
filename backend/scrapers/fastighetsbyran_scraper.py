"""
Scraper for Fastighetsbyrån (fastighetsbyran.com)
"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
from .base_scraper import BaseRealtorScraper


class FastighetsbyranScraper(BaseRealtorScraper):
    """Scraper for Fastighetsbyrån listings"""
    
    REALTOR_NAME = "Fastighetsbyrån"
    BASE_URL = "https://www.fastighetsbyran.com"
    # Filter: Stockholm, apartments only (Lägenhet)
    STOCKHOLM_SEARCH_URL = "https://www.fastighetsbyran.com/sv/sverige/till-salu?s=stockholm&propertyTypes=L%C3%A4genhet"
    
    def scrape_listings(self, max_results=50, download_images=True):
        """
        Scrape Stockholm listings from Fastighetsbyrån
        
        Args:
            max_results: Maximum number of listings to scrape
            download_images: Whether to download listing images
            
        Returns:
            List of listing dictionaries
        """
        driver = self._get_driver()
        listings = []
        
        try:
            print(f"🏠 Scraping {self.REALTOR_NAME}...")
            print(f"   URL: {self.STOCKHOLM_SEARCH_URL}")
            
            driver.get(self.STOCKHOLM_SEARCH_URL)
            time.sleep(3)
            
            # Accept cookies
            self._accept_cookies(driver)
            time.sleep(2)
            
            # Scroll to load more listings
            print("   Loading listings...")
            last_count = 0
            for _ in range(5):  # Scroll a few times to load more
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Count current listings
                listing_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/objekt/']")
                if len(listing_links) == last_count:
                    break
                last_count = len(listing_links)
                
                if last_count >= max_results:
                    break
            
            # Parse page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all listing links
            listing_links = soup.select("a[href*='/objekt/']")
            
            # Get unique URLs (filter Stockholm only)
            unique_urls = {}
            for link in listing_links:
                href = link.get('href', '')
                if '/objekt/' in href and 'objektID=' in href:
                    # Extract object ID
                    match = re.search(r'objektID=(\d+)', href)
                    if match:
                        obj_id = match.group(1)
                        if obj_id not in unique_urls:
                            full_url = href if href.startswith('http') else self.BASE_URL + href
                            unique_urls[obj_id] = full_url
            
            print(f"   Found {len(unique_urls)} unique listings")
            
            # Limit results
            urls_to_scrape = list(unique_urls.items())[:max_results]
            
            # Scrape each listing
            scraped_count = 0
            for i, (obj_id, url) in enumerate(urls_to_scrape):
                if scraped_count >= max_results:
                    break
                    
                print(f"   [{scraped_count+1}/{max_results}] Scraping {obj_id}...")
                
                listing_data = self._scrape_listing_details(driver, url, obj_id)
                
                if listing_data:
                    # Filter: only inner Stockholm apartments
                    if not self._is_inner_stockholm(listing_data.get('address'), listing_data.get('area')):
                        print(f"      Skipping: not inner Stockholm")
                        continue
                    if not self._is_apartment(listing_data.get('property_type'), listing_data.get('address', '')):
                        print(f"      Skipping: not apartment")
                        continue
                    
                    # Download images if requested
                    if download_images and listing_data.get('image_urls'):
                        print(f"      Downloading {len(listing_data['image_urls'])} images...")
                        local_paths = self._download_images(
                            f"fb_{obj_id}",
                            listing_data['image_urls']
                        )
                        listing_data['local_image_paths'] = local_paths
                    
                    listings.append(listing_data)
                    scraped_count += 1
                
                time.sleep(1.5)  # Be polite
            
            print(f"✅ Scraped {len(listings)} listings from {self.REALTOR_NAME}")
            
        except Exception as e:
            print(f"❌ Error scraping {self.REALTOR_NAME}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()
        
        return listings
    
    def _parse_listing_card(self, card_element):
        """Parse a listing card - not used for Fastighetsbyrån as we go directly to detail pages"""
        pass
    
    def _scrape_listing_details(self, driver, url, obj_id):
        """
        Scrape full details from a listing page
        
        Args:
            driver: Selenium WebDriver instance
            url: URL of the listing
            obj_id: Object ID from Fastighetsbyrån
            
        Returns:
            Dictionary with full listing details
        """
        try:
            driver.get(url)
            time.sleep(3)
            
            # Accept cookies if present
            self._accept_cookies(driver)
            time.sleep(1)
            
            # Scroll to load lazy content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Check for 404
            if "letade och letade" in soup.get_text():
                print(f"      Listing {obj_id} no longer available")
                return None
            
            listing = self.get_listing_schema()
            listing['source_id'] = obj_id
            listing['url'] = url
            
            # Primary method: Extract from JSON-LD structured data
            json_ld_scripts = soup.select('script[type="application/ld+json"]')
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                    data = json.loads(script.string)
                    
                    # Check if this is the RealEstateListing
                    types = data.get('@type', [])
                    if isinstance(types, str):
                        types = [types]
                    
                    if 'RealEstateListing' in types or 'Apartment' in types or 'House' in types:
                        listing['raw_data'] = data
                        
                        # Extract name (usually "Area, City, Street")
                        name = data.get('name', '')
                        if name:
                            listing['address'] = name
                        
                        # Description
                        listing['description'] = data.get('description')
                        
                        # Price from offers
                        if 'Offer' in types:
                            listing['asking_price'] = self._clean_price(str(data.get('price', '')))
                        
                        # Floor area
                        floor_size = data.get('floorSize', {})
                        if isinstance(floor_size, dict):
                            listing['size_sqm'] = floor_size.get('value')
                        
                        # Number of rooms
                        listing['rooms'] = data.get('numberOfRooms')
                        
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
                            street = address_data.get('streetAddress', '')
                            locality = address_data.get('addressLocality', '')
                            if street:
                                listing['address'] = street
                            if locality:
                                listing['area'] = locality
                        
                        break
                except Exception as e:
                    continue
            
            # Fallback: Parse HTML for additional data
            if not listing['asking_price']:
                # Look for price in page
                text = soup.get_text()
                price_match = re.search(r'(\d[\d\s]*)\s*kr', text)
                if price_match:
                    listing['asking_price'] = self._clean_price(price_match.group(1))
            
            if not listing['monthly_fee']:
                text = soup.get_text()
                fee_match = re.search(r'avgift[:\s]*(\d[\d\s]*)\s*kr', text, re.I)
                if fee_match:
                    listing['monthly_fee'] = self._clean_price(fee_match.group(1))
            
            # Get more images from page if JSON-LD didn't have many
            if len(listing.get('image_urls', [])) < 5:
                # Look for image gallery
                img_elements = soup.select('img[src*="bilder"], img[src*="images"], picture source, img[data-src]')
                for img in img_elements:
                    src = img.get('src') or img.get('srcset', '').split()[0] or img.get('data-src')
                    if src and 'logo' not in src.lower() and 'icon' not in src.lower():
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = self.BASE_URL + src
                        if src not in listing.get('image_urls', []):
                            listing.setdefault('image_urls', []).append(src)
                
                # Limit images
                listing['image_urls'] = listing.get('image_urls', [])[:25]
            
            # Extract agent info from page
            if not listing.get('agent_name'):
                # Look for agent section
                agent_section = soup.select_one('[class*="agent"], [class*="broker"], [class*="maklare"]')
                if agent_section:
                    agent_name = agent_section.select_one('h3, h4, [class*="name"]')
                    if agent_name:
                        listing['agent_name'] = agent_name.get_text(strip=True)
            
            return listing
            
        except Exception as e:
            print(f"      Error scraping {url}: {e}")
            import traceback
            traceback.print_exc()
            return None
