"""Debug script to inspect Hemnet's HTML structure"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup

# Initialize Chrome
chrome_options = Options()
# chrome_options.add_argument("--headless=new")  # Comment out to see the browser
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)

try:
    # Navigate to Hemnet search for Vasastan
    url = "https://www.hemnet.se/bostader?location_ids[]=17744&item_types[]=bostadsratt"
    print(f"Navigating to: {url}")
    driver.get(url)

    # Handle cookies
    try:
        time.sleep(3)
        accept_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Godkänn') or contains(text(), 'Acceptera')]")
        if accept_buttons:
            print("Accepting cookies...")
            accept_buttons[0].click()
            time.sleep(2)
    except Exception as e:
        print(f"No cookie banner: {e}")

    # Wait for page to load
    time.sleep(5)

    # Get page source
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Save HTML to file for inspection
    with open('hemnet_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("Saved page HTML to hemnet_page.html")

    # Try to find listing containers
    print("\n=== Looking for listing elements ===")

    # Try various selectors
    selectors_to_try = [
        'article',
        'li',
        'div[class*="property"]',
        'div[class*="listing"]',
        'div[class*="result"]',
        'a[href*="/bostad/"]',
        '[data-test]',
        'div[class*="card"]',
    ]

    for selector in selectors_to_try:
        elements = soup.select(selector)
        print(f"\n{selector}: Found {len(elements)} elements")
        if elements and len(elements) < 50:  # Don't print too many
            for i, elem in enumerate(elements[:3]):
                print(f"  [{i}] Tag: {elem.name}, Classes: {elem.get('class', [])}, Data attrs: {[k for k in elem.attrs if k.startswith('data-')]}")

    # Look specifically for links to listings
    print("\n=== Looking for listing links ===")
    links = soup.select('a[href*="/bostad/"]')
    print(f"Found {len(links)} links containing '/bostad/'")
    for i, link in enumerate(links[:5]):
        print(f"  [{i}] href: {link.get('href')}, text: {link.get_text(strip=True)[:50]}")

    print("\n=== Page title ===")
    print(driver.title)

finally:
    driver.quit()
    print("Done! Check hemnet_page.html for full page source.")
