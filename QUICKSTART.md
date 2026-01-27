# Booli Apartment Scraper - Quick Start

## Try It Right Now (Test Mode)

The app is configured to work **immediately** with mock data. No setup required!

### Option 1: Automatic Start (Recommended)

```bash
./start.sh
```

This will:
- Set up Python virtual environment
- Install all dependencies
- Start both backend and frontend
- Open your browser to http://localhost:3000

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm start
```

Then open http://localhost:3000 and click "Search Apartments"

You'll see 5 mock apartments with addresses, agents, and prices!

---

## What You Built

A complete web application with:

1. **Backend (Python/Flask)**
   - Web scraper for Booli.se (using Selenium)
   - Google Custom Search API integration
   - REST API endpoint
   - Test mode with mock data

2. **Frontend (React)**
   - Search form with filters
   - Apartment cards with details
   - Links to Booli and realtor websites

3. **Testing Tools**
   - `test_scraper.py` - Inspect Booli.se HTML
   - Test mode toggle
   - Mock data for development

---

## Next Steps

### 1. To Enable Real Scraping

Follow the **SELECTOR_GUIDE.md** to:
1. Run `python test_scraper.py` to inspect Booli.se
2. Find the correct CSS selectors
3. Update `backend/scrapers/booli_scraper.py`
4. Set `TEST_MODE=false` in `backend/.env`

### 2. To Enable Google Search

Follow the **SETUP_GUIDE.md** to:
1. Get Google API credentials
2. Add them to `backend/.env`
3. Restart the backend

---

## File Structure

```
booli_scraping_test/
├── QUICKSTART.md          ← You are here
├── SETUP_GUIDE.md         ← Full setup instructions
├── SELECTOR_GUIDE.md      ← How to find CSS selectors
├── start.sh               ← One-command startup
│
├── backend/
│   ├── app.py             ← Flask API server
│   ├── .env               ← Configuration (TEST_MODE, API keys)
│   ├── mock_data.py       ← Test data
│   ├── test_scraper.py    ← Booli.se inspector tool
│   ├── scrapers/
│   │   └── booli_scraper.py   ← Main scraping logic
│   └── search/
│       └── google_search.py   ← Google Custom Search
│
└── frontend/
    └── src/
        ├── App.js         ← Main React component
        └── components/
            ├── SearchForm.js      ← Search input
            ├── ApartmentList.js   ← Results list
            └── ApartmentCard.js   ← Individual card
```

---

## Key Features

- **Test Mode**: Use mock data without any setup
- **Real Scraping**: Scrape actual data from Booli.se
- **Google Search**: Find original realtor listings
- **Responsive UI**: Works on desktop and mobile
- **Error Handling**: Graceful fallbacks if scraping fails

---

## Commands Cheat Sheet

```bash
# Start everything
./start.sh

# Start backend only
cd backend && source venv/bin/activate && python app.py

# Start frontend only
cd frontend && npm start

# Inspect Booli.se
cd backend && source venv/bin/activate && python test_scraper.py

# Toggle test mode
# Edit backend/.env:
TEST_MODE=true   # Use mock data
TEST_MODE=false  # Use real scraping
```

---

## Troubleshooting

**"Backend not starting"**
- Make sure Python 3.8+ is installed: `python3 --version`
- Activate venv: `source backend/venv/bin/activate`
- Install deps: `pip install -r backend/requirements.txt`

**"Frontend not starting"**
- Make sure Node 16+ is installed: `node --version`
- Install deps: `cd frontend && npm install`

**"Cannot connect to backend"**
- Make sure backend is running on port 5000
- Check `frontend/package.json` has `"proxy": "http://localhost:5000"`

**"Scraper not working"**
- Install ChromeDriver: `brew install chromedriver`
- Run `python test_scraper.py` to debug
- Check CSS selectors in `booli_scraper.py`

---

## Important Notes

⚠️ **Web Scraping Disclaimer**
- Review Booli.se's terms of service before scraping
- Respect robots.txt
- Use reasonable delays between requests
- This tool is for educational purposes

⚠️ **Google API Limits**
- Free tier: 100 queries/day
- Monitor usage in Google Cloud Console

---

## What's Next?

1. **Try the test mode** - See if the app works
2. **Inspect Booli.se** - Find correct selectors
3. **Enable scraping** - Update selectors and toggle test mode
4. **Add Google API** - Get realtor listings
5. **Customize** - Add features, improve UI, etc.

For detailed instructions, see:
- **SETUP_GUIDE.md** - Complete setup
- **SELECTOR_GUIDE.md** - Finding CSS selectors
- **README.md** - Full documentation

---

**Questions?** Check the documentation files or inspect the code!
