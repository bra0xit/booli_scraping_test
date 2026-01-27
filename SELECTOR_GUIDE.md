# CSS Selector Guide for Booli.se

This guide will help you find the correct CSS selectors for scraping Booli.se.

## Step 1: Run the Inspection Script

```bash
cd backend
source venv/bin/activate
python test_scraper.py
```

This will:
- Open Booli.se in Chrome
- Save two HTML files: `booli_page_source.html` and `booli_detail_page.html`
- Print useful information about the page structure
- Keep the browser open so you can inspect it

## Step 2: Inspect with Browser DevTools

While the browser is open:

1. **Right-click on an apartment listing** → "Inspect Element"
2. Look at the HTML structure in DevTools
3. Find the patterns for:
   - Container for each apartment listing
   - Link to the detail page
   - Any data attributes

### What to look for on the LISTING PAGE:

- **Listing Container**: Look for repeating elements (might be `<article>`, `<div class="listing">`, etc.)
- **Listing Link**: Find the `<a>` tag that links to `/annons/[id]`
- **CSS Classes**: Note any class names that contain words like "listing", "result", "card", "item"

Example patterns to search for:
```html
<!-- Common pattern 1: Article tags -->
<article class="some-class">
  <a href="/annons/12345">...</a>
</article>

<!-- Common pattern 2: Div with class -->
<div class="listing-card">
  <a href="/annons/12345">...</a>
</div>

<!-- Common pattern 3: Data attributes -->
<div data-listing-id="12345">
  <a href="/annons/12345">...</a>
</div>
```

## Step 3: Inspect the Detail Page

On the detail page, find selectors for:

### Address
Usually in an `<h1>` or prominent heading. Example:
```html
<h1 class="property-address">Strandvägen 7A, Östermalm, Stockholm</h1>
```

### Sold Price
Look for text containing "Slutpris" or "Såld för". Example:
```html
<div class="price-info">
  <span class="label">Slutpris</span>
  <span class="value">8 500 000 kr</span>
</div>
```

### Agent/Broker Info
Look for text containing "Mäklare" or "Ansvarig mäklare". Example:
```html
<div class="broker-info">
  <span class="label">Ansvarig mäklare</span>
  <span class="name">Anna Andersson</span>
</div>
```

### Agency
Look for agency/company name, might be in a logo or text. Example:
```html
<div class="agency">
  <span>Svensk Fastighetsförmedling</span>
</div>
```

## Step 4: Update booli_scraper.py

Open `backend/scrapers/booli_scraper.py` and update the selectors.

### Location 1: Finding Listing Links (around line 58)

```python
# BEFORE (placeholder):
listing_elements = soup.find_all('a', href=lambda x: x and '/annons/' in x)

# AFTER (example - adjust based on what you found):
# Option A: If listings are in <article> tags
listing_elements = soup.select('article a[href*="/annons/"]')

# Option B: If listings have specific class
listing_elements = soup.select('.listing-card a')

# Option C: Multiple possibilities
listing_elements = soup.find_all('a', href=lambda x: x and '/annons/' in x)
```

### Location 2: Extracting Detail Page Data (around lines 95-125)

Update each section based on what you found:

```python
# ADDRESS - Update this selector
# BEFORE:
address_elem = soup.find('h1') or soup.find(class_=lambda x: x and 'address' in x.lower())

# AFTER (example):
address_elem = soup.select_one('h1.property-address')  # Use your actual class
if address_elem:
    apartment['address'] = address_elem.get_text(strip=True)

# SOLD PRICE - Update this selector
# Look for the element containing sold price
price_elem = soup.find(text=lambda x: x and 'Slutpris' in x if x else False)
if price_elem:
    # Navigate to parent to get the actual price value
    parent = price_elem.find_parent()
    # You might need to find siblings or specific child elements
    value_elem = parent.find_next_sibling('span', class_='value')
    if value_elem:
        apartment['sold_price'] = value_elem.get_text(strip=True)

# AGENT - Update this selector
agent_elem = soup.find(text=lambda x: x and 'mäklare' in x.lower() if x else False)
if agent_elem:
    parent = agent_elem.find_parent()
    # Find the actual name element
    name_elem = parent.find('span', class_='broker-name')  # Use your actual selector
    if name_elem:
        apartment['agent'] = name_elem.get_text(strip=True)

# AGENCY - Update this selector
agency_elem = soup.select_one('.agency-name')  # Use your actual selector
if agency_elem:
    apartment['agency'] = agency_elem.get_text(strip=True)
```

## Step 5: Test Your Selectors

### Option A: Test in Python Console

```python
from bs4 import BeautifulSoup

# Load the saved HTML
with open('booli_detail_page.html', 'r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Test your selectors
address = soup.select_one('h1.your-class-here')
print(f"Address: {address.get_text(strip=True) if address else 'NOT FOUND'}")

# Test other selectors...
```

### Option B: Modify test_scraper.py

Add your selectors to `test_scraper.py` to see if they work before updating the main scraper.

## Common Selector Patterns

### By Class Name
```python
soup.select_one('.className')  # First match
soup.select('.className')      # All matches
```

### By ID
```python
soup.select_one('#elementId')
```

### By Attribute
```python
soup.find('div', {'data-id': 'value'})
soup.select('[data-listing-id]')
```

### By Text Content
```python
soup.find(text='Exact text')
soup.find(text=lambda x: 'partial' in x.lower() if x else False)
```

### Navigating Elements
```python
elem.find_parent()           # Go up
elem.find_next_sibling()     # Next element at same level
elem.find('span')            # First <span> inside elem
elem.select('span.price')    # CSS selector inside elem
```

## Tips

1. **Start Simple**: Get the listings first, then worry about details
2. **Use Browser DevTools**: Right-click → Inspect is your best friend
3. **Check Multiple Listings**: Make sure your selectors work for all apartments
4. **Be Specific**: Use multiple classes or attributes if needed to be unique
5. **Handle Missing Data**: Use `if elem:` checks before accessing `.get_text()`

## Example: Complete Selector Update

Here's what a complete update might look like:

```python
# In scrape_sold_apartments (line ~58)
listing_elements = soup.select('article.listing a[href*="/annons/"]')

# In _scrape_apartment_details (lines ~95-125)
def _scrape_apartment_details(self, driver, url):
    try:
        driver.get(url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        apartment = {
            'url': url,
            'address': None,
            'agent': None,
            'agency': None,
            'sold_price': None,
            'sold_date': None,
        }

        # Address
        address_elem = soup.select_one('h1.property-title')
        if address_elem:
            apartment['address'] = address_elem.get_text(strip=True)

        # Sold Price
        price_container = soup.select_one('.sold-price-container')
        if price_container:
            price_value = price_container.select_one('.price-value')
            if price_value:
                apartment['sold_price'] = price_value.get_text(strip=True)

        # Agent
        broker_section = soup.select_one('.broker-section')
        if broker_section:
            broker_name = broker_section.select_one('.broker-name')
            if broker_name:
                apartment['agent'] = broker_name.get_text(strip=True)

        # Agency
        agency_elem = soup.select_one('.agency-name')
        if agency_elem:
            apartment['agency'] = agency_elem.get_text(strip=True)

        # Sold Date
        date_elem = soup.select_one('.sold-date')
        if date_elem:
            apartment['sold_date'] = date_elem.get_text(strip=True)

        return apartment

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None
```

## Need Help?

If you're stuck:
1. Share the HTML files generated by `test_scraper.py`
2. Share screenshots from browser DevTools
3. Describe what data you're trying to extract
