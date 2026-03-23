# Cron Setup for Realtor Scrapers

## Running Scrapers Manually

```bash
cd ~/clawd/projects/booli_scraping_test/backend
source venv/bin/activate

# Run all scrapers (50 listings each, with images)
python run_scrapers.py

# Run specific scraper
python run_scrapers.py --scraper fastighetsbyran

# Run with custom limits
python run_scrapers.py --max-results 100

# Skip image downloads (faster)
python run_scrapers.py --no-images

# View database stats only
python run_scrapers.py --stats
```

## Cron Schedule (Recommended)

Add to crontab (`crontab -e`):

```cron
# Run all scrapers every 6 hours
0 */6 * * * cd /Users/alexevander/clawd/projects/booli_scraping_test/backend && /Users/alexevander/clawd/projects/booli_scraping_test/backend/venv/bin/python run_scrapers.py --max-results 100 >> /tmp/scraper.log 2>&1

# Or run specific scrapers at different times
0 6 * * * cd /path/to/backend && venv/bin/python run_scrapers.py -s fastighetsbyran
0 8 * * * cd /path/to/backend && venv/bin/python run_scrapers.py -s svenskfast
0 10 * * * cd /path/to/backend && venv/bin/python run_scrapers.py -s bjurfors
0 12 * * * cd /path/to/backend && venv/bin/python run_scrapers.py -s notar
0 14 * * * cd /path/to/backend && venv/bin/python run_scrapers.py -s husmanhagberg
```

## Available Scrapers

| Scraper | Source | Typical Listings |
|---------|--------|-----------------|
| `fastighetsbyran` | Fastighetsbyrån | ~200 |
| `svenskfast` | Svensk Fastighetsförmedling | ~35 |
| `bjurfors` | Bjurfors | ~24 |
| `notar` | Notar | ~35 |
| `husmanhagberg` | HusmanHagberg | ~18 |

## Data Storage

- **Database**: `data/all_listings.db` (SQLite)
- **Images**: `data/images/{source}_{id}/image_001.jpg`

## Monitoring

Check recent scrape runs:
```bash
python run_scrapers.py --stats
```

Or query the database:
```sql
SELECT source, started_at, status, listings_new 
FROM scrape_runs 
ORDER BY started_at DESC 
LIMIT 10;
```
