from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

from scrapers.booli_scraper import BooliScraper
from scrapers.hemnet_scraper import HemnetScraper
from search.google_search import GoogleSearcher
from mock_data import get_mock_apartments

load_dotenv()

app = Flask(__name__)
CORS(app)

# Check if we're in test mode
TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'

booli_scraper = BooliScraper()
hemnet_scraper = HemnetScraper()

# Only initialize Google searcher if we have credentials
google_api_key = os.getenv('GOOGLE_API_KEY')
google_cse_id = os.getenv('GOOGLE_CSE_ID')

if google_api_key and google_cse_id:
    google_searcher = GoogleSearcher(api_key=google_api_key, cse_id=google_cse_id)
else:
    google_searcher = None
    print("⚠️  Google API credentials not found. Google search will be disabled.")


@app.route('/api/apartments', methods=['GET'])
def get_apartments():
    """Fetch and process apartments from Booli.se"""
    try:
        # Get query parameters
        area_id = request.args.get('areaId', '115349')
        object_type = request.args.get('objectType', 'Lägenhet')
        min_price = request.args.get('minPrice', '8000000')
        max_price = request.args.get('maxPrice', '10000000')
        min_rooms = request.args.get('minRooms', '')
        max_rooms = request.args.get('maxRooms', '')
        min_area = request.args.get('minArea', '')
        max_area = request.args.get('maxArea', '')
        max_results = request.args.get('maxResults', '10')
        test_mode = request.args.get('testMode', str(TEST_MODE)).lower() == 'true'

        if test_mode:
            print("🧪 Running in TEST MODE - using mock data")
            apartments = get_mock_apartments()
        else:
            print(f"🔍 Scraping Booli.se for apartments...")
            # Scrape Booli.se
            apartments = booli_scraper.scrape_sold_apartments(
                area_id=area_id,
                object_type=object_type,
                min_price=min_price,
                max_price=max_price,
                min_rooms=min_rooms,
                max_rooms=max_rooms,
                min_area=min_area,
                max_area=max_area,
                max_results=max_results
            )

        # For each apartment, find the original realtor listing
        if google_searcher:
            print(f"🔎 Searching for realtor listings via Google...")
            for apt in apartments:
                realtor_link = google_searcher.find_realtor_listing(
                    address=apt.get('address'),
                    agent=apt.get('agent'),
                    agency=apt.get('agency')
                )
                apt['realtor_link'] = realtor_link
        else:
            print("⚠️  Skipping Google search (no credentials)")
            for apt in apartments:
                apt['realtor_link'] = None

        return jsonify({
            'success': True,
            'apartments': apartments,
            'count': len(apartments),
            'test_mode': test_mode
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/api/booli/saved', methods=['GET'])
def get_saved_booli_apartments():
    """Get saved Booli apartments from database"""
    try:
        limit = request.args.get('limit', type=int)

        apartments = booli_scraper.get_saved_apartments(limit=limit)

        return jsonify({
            'success': True,
            'apartments': apartments,
            'count': len(apartments)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/booli/stats', methods=['GET'])
def get_booli_stats():
    """Get Booli database statistics"""
    try:
        stats = booli_scraper.get_database_stats()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mappings', methods=['GET'])
def get_mappings():
    """Get all agent and agency mappings"""
    try:
        import json
        mapping_file = os.path.join(os.path.dirname(__file__), 'agent_agency_mapping.json')

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        # Also get discovered IDs from a cache file if it exists
        discovered_file = os.path.join(os.path.dirname(__file__), 'discovered_ids.json')
        discovered = {'agents': {}, 'agencies': {}}

        if os.path.exists(discovered_file):
            with open(discovered_file, 'r', encoding='utf-8') as f:
                discovered = json.load(f)

        return jsonify({
            'success': True,
            'mappings': mappings,
            'discovered': discovered
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/mappings', methods=['POST'])
def update_mappings():
    """Update agent and agency mappings"""
    try:
        import json
        data = request.get_json()

        mapping_file = os.path.join(os.path.dirname(__file__), 'agent_agency_mapping.json')

        # Read current mappings
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        # Update mappings
        if 'agents' in data:
            mappings['agents'].update(data['agents'])

        if 'agencies' in data:
            mappings['agencies'].update(data['agencies'])

        # Write back to file
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2, ensure_ascii=False)

        # Reload the scraper's mapping
        booli_scraper.agent_mapping = booli_scraper._load_mapping()

        return jsonify({
            'success': True,
            'message': 'Mappings updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/discover-ids', methods=['POST'])
def discover_ids():
    """Discover all agent/agency IDs from recent scraping"""
    try:
        import json

        # Get apartments from last scrape or do a new scrape
        area_id = request.args.get('areaId', '115349')
        min_price = request.args.get('minPrice', '8000000')
        max_price = request.args.get('maxPrice', '10000000')

        print(f"🔍 Discovering agent/agency IDs...")
        apartments = booli_scraper.scrape_sold_apartments(
            area_id=area_id,
            min_price=min_price,
            max_price=max_price
        )

        # Collect unique IDs
        discovered = {'agents': {}, 'agencies': {}}

        for apt in apartments:
            agent_url = apt.get('agent_url', '')
            agency_url = apt.get('agency_url', '')

            # Extract ID from URL
            if agent_url and '/maklare/' in agent_url:
                agent_id = agent_url.split('/maklare/')[-1]
                discovered['agents'][agent_id] = {
                    'url': agent_url,
                    'example_address': apt.get('address')
                }

            if agency_url and '/maklarbyra/' in agency_url:
                agency_id = agency_url.split('/maklarbyra/')[-1]
                discovered['agencies'][agency_id] = {
                    'url': agency_url,
                    'example_address': apt.get('address')
                }

        # Save discovered IDs to cache
        discovered_file = os.path.join(os.path.dirname(__file__), 'discovered_ids.json')
        with open(discovered_file, 'w', encoding='utf-8') as f:
            json.dump(discovered, f, indent=2, ensure_ascii=False)

        return jsonify({
            'success': True,
            'discovered': discovered,
            'count': {
                'agents': len(discovered['agents']),
                'agencies': len(discovered['agencies'])
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hemnet/scrape', methods=['POST'])
def scrape_hemnet():
    """Scrape Hemnet.se for active listings and save to database"""
    try:
        data = request.get_json() or {}

        # Get parameters
        location_ids = data.get('locationIds', ['925970'])  # Default: Vasastan, Stockholm
        property_type = data.get('propertyType', 'lägenhet')
        min_price = data.get('minPrice')
        max_price = data.get('maxPrice')
        min_rooms = data.get('minRooms')
        max_rooms = data.get('maxRooms')
        min_size = data.get('minSize')
        max_size = data.get('maxSize')
        max_results = data.get('maxResults', 10)
        download_images = data.get('downloadImages', True)

        print(f"🏠 Scraping Hemnet for {property_type} in locations: {location_ids}")

        # Scrape listings
        listings = hemnet_scraper.scrape_for_sale(
            location_ids=location_ids,
            property_type=property_type,
            min_price=min_price,
            max_price=max_price,
            min_rooms=min_rooms,
            max_rooms=max_rooms,
            min_size=min_size,
            max_size=max_size,
            max_results=max_results,
            download_images=download_images
        )

        return jsonify({
            'success': True,
            'count': len(listings),
            'message': f'Scraped and saved {len(listings)} listings'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hemnet/listings', methods=['GET'])
def get_hemnet_listings():
    """Get saved Hemnet listings from database"""
    try:
        status = request.args.get('status', 'active')
        limit = request.args.get('limit', type=int)

        listings = hemnet_scraper.get_saved_listings(status=status, limit=limit)

        return jsonify({
            'success': True,
            'listings': listings,
            'count': len(listings)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hemnet/listing/<int:listing_id>', methods=['GET'])
def get_hemnet_listing(listing_id):
    """Get a specific Hemnet listing by ID"""
    try:
        from storage.database import HemnetDatabase
        db = HemnetDatabase()

        listing = db.get_listing_by_id(listing_id)

        if not listing:
            return jsonify({
                'success': False,
                'error': 'Listing not found'
            }), 404

        return jsonify({
            'success': True,
            'listing': listing
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hemnet/stats', methods=['GET'])
def get_hemnet_stats():
    """Get Hemnet database and storage statistics"""
    try:
        stats = hemnet_scraper.get_database_stats()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hemnet/images/<path:image_path>')
def serve_hemnet_image(image_path):
    """Serve downloaded Hemnet images"""
    try:
        # Construct full path
        full_path = os.path.join(os.path.dirname(__file__), 'data', 'images', image_path)
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)

        return send_from_directory(directory, filename)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


if __name__ == '__main__':
    app.run(debug=True, port=5002)
