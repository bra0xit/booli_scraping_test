"""
Save the HTML that Selenium actually sees
"""
from scrapers.booli_scraper import BooliScraper

scraper = BooliScraper()
driver = scraper._get_driver()

try:
    url = "https://www.booli.se/annons/5848556"
    print(f"Visiting: {url}")

    driver.get(url)

    # Wait and scroll like the scraper does
    import time
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # Save the HTML
    html = driver.page_source
    with open('selenium_page.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Saved HTML to selenium_page.html")

    # Search for "Madeleine" or "Christov"
    if 'madeleine' in html.lower() or 'christov' in html.lower():
        print("\n✓ Found 'Madeleine' or 'Christov' in HTML!")
    else:
        print("\n✗ Did NOT find 'Madeleine' or 'Christov' in HTML")

    # Search for any agent-related text
    if 'ansvarig mäklare' in html.lower():
        print("✓ Found 'ansvarig mäklare' in HTML")
    else:
        print("✗ Did NOT find 'ansvarig mäklare' in HTML")

finally:
    driver.quit()
