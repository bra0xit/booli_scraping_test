"""
Detailed inspection of Booli pages with longer waits for dynamic content
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json

def inspect_page(url, expected_agent):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"\n{'='*80}")
        print(f"Inspecting: {url}")
        print(f"Expected agent: {expected_agent}")
        print('='*80)

        driver.get(url)

        # Wait longer for dynamic content
        print("Waiting for page to fully load...")
        time.sleep(5)

        # Scroll down to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Get all text content
        all_text = soup.get_text()

        # Search for the expected agent name
        if expected_agent.lower() in all_text.lower():
            print(f"\n✓ Found '{expected_agent}' in page text!")

            # Find the exact location
            words = expected_agent.split()
            for word in words:
                elements = soup.find_all(text=lambda x: x and word.lower() in str(x).lower())
                if elements:
                    print(f"\nFound '{word}' in {len(elements)} locations:")
                    for i, elem in enumerate(elements[:3]):
                        parent = elem.find_parent()
                        if parent:
                            print(f"\n  Location {i+1}:")
                            print(f"    Text: {elem.strip()[:100]}")
                            print(f"    Parent tag: {parent.name}")
                            print(f"    Parent class: {parent.get('class')}")
                            print(f"    Parent text: {parent.get_text(strip=True)[:150]}")

                            # Get parent's parent
                            grandparent = parent.find_parent()
                            if grandparent:
                                print(f"    Grandparent tag: {grandparent.name}")
                                print(f"    Grandparent class: {grandparent.get('class')}")
        else:
            print(f"\n✗ Did NOT find '{expected_agent}' in page text")
            print("\nSearching for common agent/broker indicators...")

            # Look for any text containing common Swedish realtor terms
            keywords = ['mäklare', 'ansvarig', 'förmedling', 'kontakta']
            for keyword in keywords:
                elements = soup.find_all(text=lambda x: x and keyword in str(x).lower())
                if elements:
                    print(f"\n  Found '{keyword}' ({len(elements)} times)")
                    for elem in elements[:2]:
                        parent = elem.find_parent()
                        if parent:
                            print(f"    Context: {parent.get_text(strip=True)[:200]}")

        # Also check JSON data
        print("\n" + "="*80)
        print("CHECKING JSON DATA")
        print("="*80)

        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        if script_tag:
            json_data = json.loads(script_tag.string)
            apollo_state = json_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

            # Look for any keys that might contain agent/agency data
            print("\nKeys containing 'Agent' or 'Agency':")
            for key in apollo_state.keys():
                if 'agent' in key.lower() or 'agency' in key.lower() or 'broker' in key.lower():
                    print(f"  {key}")
                    data = apollo_state[key]
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if 'name' in str(k).lower() or 'title' in str(k).lower():
                                print(f"    {k}: {v}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Test both URLs
    test_cases = [
        ("https://www.booli.se/bostad/691097", "Otilia Håkansson"),
        ("https://www.booli.se/annons/5848556", "Madeleine Christov"),
    ]

    for url, agent in test_cases:
        inspect_page(url, agent)
