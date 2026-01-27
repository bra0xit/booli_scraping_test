# Quick Setup Guide

## Step 1: Install Backend Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Test with Mock Data (No Setup Required!)

The app is already configured to run in **TEST MODE** with mock data, so you can try it immediately without any scraping or API setup.

```bash
# Make sure you're in backend/ with venv activated
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

Keep this terminal open!

## Step 3: Install Frontend Dependencies

Open a **new terminal**:

```bash
cd frontend

# Install dependencies
npm install

# Start the frontend
npm start
```

The app will open at http://localhost:3000

Click "Search Apartments" and you'll see 5 mock apartments!

---

## Step 4: Inspect Booli.se (To Enable Real Scraping)

To enable real scraping, we need to find the correct CSS selectors from Booli.se.

### Install ChromeDriver first:

```bash
# On macOS
brew install chromedriver

# On Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Or download from: https://chromedriver.chromium.org/
```

### Run the inspection script:

```bash
cd backend
source venv/bin/activate
python test_scraper.py
```

This will:
1. Open Booli.se in a browser
2. Save the HTML to files
3. Print information about the page structure
4. Help you identify the correct selectors

### Update the selectors:

After running the test, open the generated files:
- `booli_page_source.html` - Listing page HTML
- `booli_detail_page.html` - Detail page HTML

Search for apartment addresses or prices to find the HTML structure, then update:
- `backend/scrapers/booli_scraper.py` (lines 68-95)

---

## Step 5: Enable Google Search (Optional)

To find original realtor listings:

1. **Get Google API Key:**
   - Go to https://console.cloud.google.com/
   - Create a project
   - Enable "Custom Search API"
   - Create credentials → API Key

2. **Create Custom Search Engine:**
   - Go to https://programmablesearchengine.google.com/
   - Click "Add"
   - Set to search the entire web
   - Copy your "Search Engine ID"

3. **Add to .env:**
   ```bash
   # Edit backend/.env
   GOOGLE_API_KEY=your_api_key_here
   GOOGLE_CSE_ID=your_cse_id_here
   ```

4. **Restart the backend server**

---

## Step 6: Enable Real Scraping

Once you've updated the CSS selectors in `booli_scraper.py`:

```bash
# Edit backend/.env
TEST_MODE=false
```

Restart the backend server, and the app will now scrape real data from Booli.se!

---

## Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (need 3.8+)
- Make sure venv is activated: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Check Node version: `node --version` (need 16+)
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### Scraper not working
- Make sure ChromeDriver is installed and matches Chrome version
- Check console output for error messages
- Verify CSS selectors are correct by running `python test_scraper.py`

### Google Search not working
- Verify API key and CSE ID are in `.env`
- Check quota at https://console.cloud.google.com/
- Make sure Custom Search API is enabled

---

## Quick Commands Reference

```bash
# Start backend (Terminal 1)
cd backend
source venv/bin/activate
python app.py

# Start frontend (Terminal 2)
cd frontend
npm start

# Test scraper
cd backend
source venv/bin/activate
python test_scraper.py

# Switch between test/real mode
# Edit backend/.env:
# TEST_MODE=true   # Mock data
# TEST_MODE=false  # Real scraping
```
