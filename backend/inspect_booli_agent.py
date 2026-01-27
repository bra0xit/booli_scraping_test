"""
Quick script to inspect Booli detail pages for agent/agency information
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def inspect_page(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"\n{'='*80}")
        print(f"Inspecting: {url}")
        print('='*80)

        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Save HTML to file for inspection
        filename = url.split('/')[-1] + '_detail.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"Saved HTML to: {filename}")

        # Search for agent/agency info
        print("\nSearching for agent/agency information...")

        # Look for JSON data
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
        if script_tag:
            import json
            json_data = json.loads(script_tag.string)

            # Save JSON for inspection
            json_filename = url.split('/')[-1] + '_data.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"Saved JSON to: {json_filename}")

            # Look for agent/agency in Apollo state
            apollo_state = json_data.get('props', {}).get('pageProps', {}).get('__APOLLO_STATE__', {})

            print("\nSearching Apollo State for agent/agency...")
            for key, value in apollo_state.items():
                if 'agent' in key.lower() or 'agency' in key.lower() or 'broker' in key.lower():
                    print(f"\nKey: {key}")
                    print(f"Value: {value}")

                if isinstance(value, dict):
                    for k, v in value.items():
                        if 'agent' in str(k).lower() or 'agency' in str(k).lower() or 'broker' in str(k).lower() or 'mäklare' in str(k).lower():
                            print(f"\n  Found in {key}:")
                            print(f"    {k}: {v}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Inspect both example URLs
    urls = [
        "https://www.booli.se/bostad/691097",  # Otilia Håkansson, Skandiamäklarna
        "https://www.booli.se/annons/5848556",  # Madeleine Christov, HusmanHagberg
    ]

    for url in urls:
        inspect_page(url)
