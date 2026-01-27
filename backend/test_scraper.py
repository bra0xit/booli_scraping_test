"""
Test script to inspect Booli.se HTML structure
Run this to see what the actual page looks like and identify correct selectors
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time


def inspect_booli_listings():
    """Fetch and print HTML structure to help identify selectors"""

    search_url = "https://www.booli.se/sok/slutpriser?areaIds=115349&objectType=L%C3%A4genhet&minSoldPrice=8000000&maxSoldPrice=10000000"

    chrome_options = Options()
    # Comment out headless to see the browser
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"\n{'='*80}")
        print(f"Fetching: {search_url}")
        print(f"{'='*80}\n")

        driver.get(search_url)

        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(5)  # Give it time to load dynamic content

        # Save page source to file for inspection
        with open('booli_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✓ Page source saved to 'booli_page_source.html'\n")

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Try to find common patterns for listings
        print("\n" + "="*80)
        print("SEARCHING FOR LISTING PATTERNS")
        print("="*80 + "\n")

        # Pattern 1: Look for links with /annons/
        annons_links = soup.find_all('a', href=lambda x: x and '/annons/' in x)
        print(f"Found {len(annons_links)} links containing '/annons/'")
        if annons_links:
            print("\nFirst 3 /annons/ links:")
            for i, link in enumerate(annons_links[:3]):
                print(f"\n  Link {i+1}:")
                print(f"    href: {link.get('href')}")
                print(f"    class: {link.get('class')}")
                print(f"    text: {link.get_text(strip=True)[:100]}...")

        # Pattern 2: Look for article tags
        articles = soup.find_all('article')
        print(f"\n\nFound {len(articles)} <article> tags")
        if articles:
            print("\nFirst article tag:")
            print(articles[0].prettify()[:500])

        # Pattern 3: Look for divs with 'sold', 'listing', 'result' in class
        search_classes = ['sold', 'listing', 'result', 'card', 'item']
        for cls in search_classes:
            elements = soup.find_all(class_=lambda x: x and cls in str(x).lower())
            if elements:
                print(f"\n\nFound {len(elements)} elements with '{cls}' in class name")
                if elements:
                    print(f"First element class: {elements[0].get('class')}")

        # Pattern 4: Look for data attributes
        data_attrs = soup.find_all(attrs=lambda x: any(k.startswith('data-') for k in x.keys()) if x else False)
        print(f"\n\nFound {len(data_attrs)} elements with data- attributes")
        if data_attrs:
            print("Sample data attributes:")
            for elem in data_attrs[:5]:
                data_keys = [k for k in elem.attrs.keys() if k.startswith('data-')]
                if data_keys:
                    print(f"  {elem.name}: {data_keys}")

        print("\n\n" + "="*80)
        print("Now let's try to fetch a detail page...")
        print("="*80 + "\n")

        # If we found any annons links, try the first one
        if annons_links:
            detail_url = annons_links[0].get('href')
            if not detail_url.startswith('http'):
                detail_url = 'https://www.booli.se' + detail_url

            print(f"Fetching detail page: {detail_url}")
            driver.get(detail_url)
            time.sleep(3)

            # Save detail page
            with open('booli_detail_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("✓ Detail page saved to 'booli_detail_page.html'\n")

            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Look for common detail page elements
            print("\nLooking for address (h1, h2 tags):")
            for tag in ['h1', 'h2']:
                headers = detail_soup.find_all(tag)
                if headers:
                    print(f"  {tag}: {headers[0].get_text(strip=True)}")

            print("\nLooking for price information:")
            price_keywords = ['pris', 'slutpris', 'price', 'sold']
            for keyword in price_keywords:
                elements = detail_soup.find_all(text=lambda x: x and keyword.lower() in x.lower())
                if elements:
                    print(f"  '{keyword}': Found {len(elements)} matches")
                    for elem in elements[:2]:
                        print(f"    - {elem.strip()[:80]}")

            print("\nLooking for agent/broker information:")
            agent_keywords = ['mäklare', 'broker', 'agent', 'ansvarig']
            for keyword in agent_keywords:
                elements = detail_soup.find_all(text=lambda x: x and keyword.lower() in x.lower())
                if elements:
                    print(f"  '{keyword}': Found {len(elements)} matches")
                    for elem in elements[:2]:
                        parent = elem.find_parent()
                        if parent:
                            print(f"    - {parent.get_text(strip=True)[:80]}")

        print("\n\n" + "="*80)
        print("INSPECTION COMPLETE")
        print("="*80)
        print("\nFiles created:")
        print("  1. booli_page_source.html - Full listing page HTML")
        print("  2. booli_detail_page.html - Full detail page HTML")
        print("\nNext steps:")
        print("  1. Open these HTML files in a text editor")
        print("  2. Search for apartment addresses/prices to find the right selectors")
        print("  3. Update backend/scrapers/booli_scraper.py with correct selectors")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        input("\n\nPress Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    inspect_booli_listings()
