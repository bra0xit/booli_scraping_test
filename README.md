# Booli Apartment Scraper

A web application that scrapes sold apartment listings from Booli.se and finds their original realtor listings via Google Search.

## Features

- Scrapes sold apartment listings from Booli.se
- Extracts apartment details (address, agent, agency, price, date)
- Uses Google Custom Search API to find original realtor listings
- Clean React frontend to display results
- Links directly to both Booli listing and realtor website

## Tech Stack

**Backend:**
- Python 3.x
- Flask (API server)
- Selenium (web scraping)
- BeautifulSoup4 (HTML parsing)
- Google Custom Search API

**Frontend:**
- React
- CSS3

## Prerequisites

1. **Python 3.8+**
2. **Node.js 16+** and npm
3. **Chrome Browser** (for Selenium)
4. **ChromeDriver** - Download from https://chromedriver.chromium.org/
5. **Google Custom Search API credentials:**
   - API Key from https://console.cloud.google.com/
   - Custom Search Engine ID from https://programmablesearchengine.google.com/

## Setup Instructions

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your credentials
# GOOGLE_API_KEY=your_api_key_here
# GOOGLE_CSE_ID=your_cse_id_here
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 3. Google Custom Search Setup

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable "Custom Search API"
4. Create credentials (API Key)
5. Go to https://programmablesearchengine.google.com/
6. Create a new search engine
7. Set it to search the entire web
8. Copy your Search Engine ID

Add both to `backend/.env`

## Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate
python app.py
```

Backend will run on http://localhost:5000

### Start Frontend (Terminal 2)

```bash
cd frontend
npm start
```

Frontend will open on http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Enter search parameters:
   - **Area ID**: Booli.se area identifier (default: 115349)
   - **Min Price**: Minimum sold price in SEK
   - **Max Price**: Maximum sold price in SEK
3. Click "Search Apartments"
4. Wait for results (may take 1-2 minutes)
5. View apartments with links to:
   - Original Booli listing
   - Realtor website listing (when found)

## Important Notes

### Web Scraping Considerations

- **Booli.se Terms of Service**: Please review Booli.se's terms of service and robots.txt before scraping
- **Rate Limiting**: The scraper includes delays to be respectful to the server
- **Selectors**: HTML selectors in `booli_scraper.py` are placeholders and need adjustment based on actual page structure
- **Legal**: Web scraping may have legal implications - ensure you have the right to scrape the target website

### Google API Limits

- **Free tier**: 100 queries per day
- **Paid tier**: Up to 10,000 queries per day
- Monitor your usage at https://console.cloud.google.com/

### ChromeDriver

- Ensure ChromeDriver version matches your Chrome browser version
- Add ChromeDriver to your PATH, or update `booli_scraper.py` to specify the path

## Customization

### Adjusting Scraper Selectors

The HTML selectors in `backend/scrapers/booli_scraper.py` need to be adjusted to match Booli.se's actual structure:

```python
# Lines 68-95 in booli_scraper.py
# Update these selectors based on actual HTML
```

### Realtor Domains

Add more Swedish realtor domains in `backend/search/google_search.py`:

```python
realtor_domains = [
    'hemnet.se',
    'svenskfast.se',
    # Add more domains here
]
```

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version`
- Ensure virtual environment is activated
- Verify all dependencies installed: `pip list`

**Scraper not finding apartments:**
- Check Booli.se URL is accessible
- Verify ChromeDriver is installed and in PATH
- Check console output for error messages
- Update CSS selectors to match current HTML structure

**Google Search not working:**
- Verify API key and CSE ID in `.env`
- Check API quota at Google Cloud Console
- Ensure Custom Search API is enabled

**Frontend not connecting to backend:**
- Verify backend is running on port 5000
- Check browser console for CORS errors
- Ensure proxy setting in `frontend/package.json` is correct

## Future Enhancements

- [ ] Add caching to avoid re-scraping
- [ ] Implement pagination for search results
- [ ] Add database to store results
- [ ] Better error handling and retry logic
- [ ] More detailed apartment information
- [ ] Export results to CSV/JSON
- [ ] User authentication
- [ ] Scheduled scraping jobs

## License

MIT

## Disclaimer

This tool is for educational purposes. Always respect website terms of service and robots.txt. The authors are not responsible for any misuse of this software.
