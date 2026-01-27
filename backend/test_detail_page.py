"""
Test script to inspect a single Booli detail page for agent/broker info
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def inspect_detail_page():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    # Use one of the URLs from the listing page
    url = "https://www.booli.se/annons/5848556"  # Gästrikegatan 22

    try:
        print(f"Fetching: {url}")
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Save to file
        with open('detail_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("Saved to detail_page.html")

        # Search for agent/broker keywords
        print("\n" + "="*80)
        print("SEARCHING FOR AGENT/BROKER INFORMATION")
        print("="*80 + "\n")

        keywords = ['mäklare', 'ansvarig', 'broker', 'agent', 'förmedlare']

        for keyword in keywords:
            elements = soup.find_all(text=lambda x: x and keyword.lower() in str(x).lower())
            if elements:
                print(f"\nFound '{keyword}' ({len(elements)} matches):")
                for i, elem in enumerate(elements[:3]):  # First 3 matches
                    parent = elem.find_parent()
                    if parent:
                        print(f"\n  Match {i+1}:")
                        print(f"    Text: {elem.strip()[:100]}")
                        print(f"    Parent tag: {parent.name}")
                        print(f"    Parent class: {parent.get('class')}")
                        print(f"    Parent text: {parent.get_text(strip=True)[:150]}")

                        # Try to find sibling or nearby elements
                        next_sibling = parent.find_next_sibling()
                        if next_sibling:
                            print(f"    Next sibling: {next_sibling.get_text(strip=True)[:100]}")

        print("\n" + "="*80)
        print("LOOKING FOR COMMON REALTOR PATTERNS")
        print("="*80 + "\n")

        # Look for sections that might contain realtor info
        sections = soup.find_all(['section', 'div', 'article'], class_=lambda x: x and any(
            term in str(x).lower() for term in ['broker', 'agent', 'contact', 'mäklare', 'säljare']
        ))

        print(f"Found {len(sections)} sections with broker-related classes")
        for i, section in enumerate(sections[:5]):
            print(f"\nSection {i+1}:")
            print(f"  Tag: {section.name}")
            print(f"  Class: {section.get('class')}")
            print(f"  Text: {section.get_text(strip=True)[:200]}")

    finally:
        driver.quit()

if __name__ == "__main__":
    inspect_detail_page()
