# Agent & Agency Mapping Guide

## How It Works

Since Booli.se blocks automated scraping of agent/agency names, we use a manual mapping approach:

1. **The scraper extracts agent/agency IDs** from Booli's JSON data (this works reliably)
2. **You manually provide the names** for these IDs in a mapping file
3. **The scraper looks up the names** from your mapping and displays them

## Step-by-Step Process

### 1. First Run - Collect IDs

Run the app normally to scrape apartments:

```bash
cd backend
source venv/bin/activate
python collect_ids.py
```

This will:
- Scrape all apartments in your search criteria
- Extract all unique agent and agency IDs
- Show you which IDs are missing from the mapping
- Provide direct links to the Hittamäklare profiles

### 2. Add Names to Mapping

Open `backend/agent_agency_mapping.json` and add the missing IDs:

```json
{
  "agents": {
    "11542": "Otilia Håkansson",
    "11223": "Madeleine Christov",
    "12345": "New Agent Name Here"
  },
  "agencies": {
    "32": "Skandiamäklarna",
    "16": "Husman Hagberg",
    "67": "New Agency Name Here"
  }
}
```

**How to find the names:**
- Visit the Hittamäklare profile URLs provided by `collect_ids.py`
- Or visit the Booli listing manually in your browser to see the agent/agency names
- Copy the exact names into the mapping file

### 3. Restart and Scrape

Restart the backend server (it will automatically load the updated mapping):

```bash
# The server will automatically restart if running in debug mode
# Or manually restart:
python app.py
```

Now when you scrape, the agent and agency names will appear!

## Maintenance

- **New agents/agencies appear?** Just run `collect_ids.py` again to see which ones are missing
- **Limited area scraping** means you'll likely only have 10-20 agents/agencies total
- **Once mapped**, the names will work for all future scrapes

## Fallback Behavior

If an agent or agency ID is not in the mapping, the scraper will display:
- `Agent ID: 11542`
- `Agency ID: 32`

This way you can still see the listings and add the names later.

## Example Workflow

```bash
# 1. Scrape and collect IDs
cd backend
source venv/bin/activate
python collect_ids.py

# Output:
# Missing 3 agent(s) in mapping:
#   - Agent ID: 99999
#     Profile: https://www.hittamaklare.se/maklare/99999

# 2. Visit the profile in your browser, see the name is "John Doe"

# 3. Edit agent_agency_mapping.json:
{
  "agents": {
    "99999": "John Doe"
  }
}

# 4. Restart server and scrape again - names now appear!
```
