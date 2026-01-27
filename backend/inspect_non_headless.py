"""
Try inspecting without headless mode
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

chrome_options = Options()
# Don't use headless
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

try:
    url = "https://www.booli.se/bostad/691097"
    print(f"Opening: {url}")
    print("A browser window will open. Check if you can see 'Otilia Håkansson' on the page.")
    print("Waiting 10 seconds for you to inspect...")

    driver.get(url)
    time.sleep(10)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Search for the agent name
    all_text = soup.get_text()
    if "Otilia" in all_text or "Håkansson" in all_text:
        print("\n✓ Found agent name in non-headless mode!")

        # Find it
        elements = soup.find_all(string=lambda x: x and ('otilia' in str(x).lower() or 'håkansson' in str(x).lower()))
        for elem in elements:
            parent = elem.find_parent()
            if parent:
                print(f"\nFound: {elem.strip()}")
                print(f"Parent tag: {parent.name}")
                print(f"Parent class: {parent.get('class')}")
    else:
        print("\n✗ Still no agent name in non-headless mode")

        # Save HTML for manual inspection
        with open('non_headless_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("Saved to non_headless_page.html")

finally:
    driver.quit()
