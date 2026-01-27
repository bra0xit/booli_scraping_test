"""
Quick test to verify agent/agency extraction from Booli pages
"""
from scrapers.booli_scraper import BooliScraper

scraper = BooliScraper()
driver = scraper._get_driver()

try:
    # Test with the URLs you provided
    test_urls = [
        "https://www.booli.se/bostad/691097",  # Expected: Otilia Håkansson, Skandiamäklarna
        "https://www.booli.se/annons/5848556",  # Expected: Madeleine Christov, HusmanHagberg
    ]

    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"Testing: {url}")
        print('='*80)

        apartment = scraper._scrape_apartment_details(driver, url)

        if apartment:
            print(f"\nResults:")
            print(f"  Address: {apartment.get('address')}")
            print(f"  Agent: {apartment.get('agent')}")
            print(f"  Agent URL: {apartment.get('agent_url')}")
            print(f"  Agency: {apartment.get('agency')}")
            print(f"  Agency URL: {apartment.get('agency_url')}")
            print(f"  Sold Price: {apartment.get('sold_price')}")
            print(f"  Sold Date: {apartment.get('sold_date')}")
        else:
            print("Failed to scrape apartment details")

finally:
    driver.quit()
