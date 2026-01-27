"""
Helper script to collect all unique agent and agency IDs from the scraping results
Run this after scraping to see which IDs you need to add to agent_agency_mapping.json
"""
from scrapers.booli_scraper import BooliScraper
import json

# Configuration - same as your main scraping parameters
AREA_ID = '115349'  # Vasastan
MIN_PRICE = '8000000'
MAX_PRICE = '10000000'

print("="*80)
print("Collecting all unique agent and agency IDs...")
print("="*80)

scraper = BooliScraper()

# Scrape apartments
apartments = scraper.scrape_sold_apartments(
    area_id=AREA_ID,
    min_price=MIN_PRICE,
    max_price=MAX_PRICE
)

# Collect unique IDs
agent_ids = set()
agency_ids = set()

for apt in apartments:
    agent_url = apt.get('agent_url', '')
    agency_url = apt.get('agency_url', '')

    # Extract ID from URL
    if agent_url and '/maklare/' in agent_url:
        agent_id = agent_url.split('/maklare/')[-1]
        agent_ids.add(agent_id)

    if agency_url and '/maklarbyra/' in agency_url:
        agency_id = agency_url.split('/maklarbyra/')[-1]
        agency_ids.add(agency_id)

print(f"\n{'='*80}")
print(f"Found {len(agent_ids)} unique agents and {len(agency_ids)} unique agencies")
print(f"{'='*80}\n")

# Load current mapping
with open('agent_agency_mapping.json', 'r', encoding='utf-8') as f:
    current_mapping = json.load(f)

# Find missing IDs
missing_agents = [aid for aid in agent_ids if aid not in current_mapping['agents']]
missing_agencies = [aid for aid in agency_ids if aid not in current_mapping['agencies']]

if missing_agents:
    print(f"Missing {len(missing_agents)} agent(s) in mapping:")
    for aid in sorted(missing_agents):
        print(f"  - Agent ID: {aid}")
        print(f"    Profile: https://www.hittamaklare.se/maklare/{aid}")
    print()

if missing_agencies:
    print(f"Missing {len(missing_agencies)} agencie(s) in mapping:")
    for aid in sorted(missing_agencies):
        print(f"  - Agency ID: {aid}")
        print(f"    Profile: https://www.hittamaklare.se/maklarbyra/{aid}")
    print()

if not missing_agents and not missing_agencies:
    print("✓ All agent and agency IDs are in the mapping!")
    print()

print("="*80)
print("To add missing IDs, edit backend/agent_agency_mapping.json")
print("Visit the profile URLs above in your browser to see the names")
print("="*80)
