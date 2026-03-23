#!/usr/bin/env python3
"""
Scraper runner - runs all realtor scrapers and stores results
Can be run via cron for regular updates
"""

import sys
import os
import argparse
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage.listings_database import ListingsDatabase
from scrapers.fastighetsbyran_scraper import FastighetsbyranScraper
from scrapers.svenskfast_scraper import SvenskfastScraper
from scrapers.bjurfors_scraper import BjurforsScraper
from scrapers.notar_scraper import NotarScraper
from scrapers.husmanhagberg_scraper import HusmanHagbergScraper

# Available scrapers
SCRAPERS = {
    'fastighetsbyran': FastighetsbyranScraper,
    'svenskfast': SvenskfastScraper,
    'bjurfors': BjurforsScraper,
    'notar': NotarScraper,
    'husmanhagberg': HusmanHagbergScraper,
}


def run_scraper(name: str, scraper_class, db: ListingsDatabase, 
                max_results: int = 50, download_images: bool = True):
    """Run a single scraper and save results to database"""
    print(f"\n{'='*60}")
    print(f"Starting {name} scraper at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Start scrape run
    run_id = db.start_scrape_run(name)
    
    stats = {'found': 0, 'new': 0, 'updated': 0, 'images': 0}
    error = None
    
    try:
        scraper = scraper_class()
        listings = scraper.scrape_listings(
            max_results=max_results,
            download_images=download_images
        )
        
        stats['found'] = len(listings)
        active_ids = []
        
        for listing in listings:
            listing_id, is_new = db.upsert_listing(listing)
            active_ids.append(listing['source_id'])
            
            if is_new:
                stats['new'] += 1
            else:
                stats['updated'] += 1
            
            # Save images
            if listing.get('image_urls'):
                db.add_images(
                    listing_id, 
                    listing['image_urls'],
                    listing.get('local_image_paths')
                )
                if listing.get('local_image_paths'):
                    stats['images'] += len([p for p in listing['local_image_paths'] if p])
        
        # Mark listings not seen as inactive
        # db.mark_inactive(name, active_ids)  # Uncomment when ready
        
        print(f"\n✅ {name} completed: {stats['found']} found, {stats['new']} new, {stats['updated']} updated")
        
    except Exception as e:
        error = str(e)
        print(f"\n❌ {name} failed: {error}")
        import traceback
        traceback.print_exc()
    
    # Finish scrape run
    db.finish_scrape_run(run_id, stats, error)
    
    return stats


def run_all_scrapers(max_results: int = 50, download_images: bool = True):
    """Run all available scrapers"""
    db = ListingsDatabase()
    
    print(f"\n🚀 Starting scraper run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Max results per scraper: {max_results}")
    print(f"   Download images: {download_images}")
    
    total_stats = {'found': 0, 'new': 0, 'updated': 0, 'images': 0}
    
    for name, scraper_class in SCRAPERS.items():
        stats = run_scraper(name, scraper_class, db, max_results, download_images)
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
    
    print(f"\n{'='*60}")
    print(f"📊 TOTAL: {total_stats['found']} found, {total_stats['new']} new, {total_stats['images']} images")
    print(f"{'='*60}")
    
    # Print database stats
    db_stats = db.get_stats()
    print(f"\n📁 Database stats:")
    print(f"   Active listings: {db_stats['active_listings']}")
    print(f"   Downloaded images: {db_stats['downloaded_images']}")
    print(f"   By source: {db_stats['by_source']}")
    
    return total_stats


def main():
    parser = argparse.ArgumentParser(description='Run realtor scrapers')
    parser.add_argument('--scraper', '-s', choices=list(SCRAPERS.keys()) + ['all'],
                       default='all', help='Which scraper to run (default: all)')
    parser.add_argument('--max-results', '-m', type=int, default=50,
                       help='Maximum results per scraper (default: 50)')
    parser.add_argument('--no-images', action='store_true',
                       help='Skip image downloads')
    parser.add_argument('--stats', action='store_true',
                       help='Just show database stats')
    
    args = parser.parse_args()
    
    if args.stats:
        db = ListingsDatabase()
        stats = db.get_stats()
        print(f"\n📊 Database Statistics:")
        print(f"   Active listings: {stats['active_listings']}")
        print(f"   Downloaded images: {stats['downloaded_images']}")
        print(f"   By source:")
        for source, count in stats.get('by_source', {}).items():
            print(f"      {source}: {count}")
        print(f"\n   Recent runs:")
        for run in stats.get('recent_runs', [])[:5]:
            print(f"      {run['started_at']} - {run['source']}: {run['status']} ({run['new']} new)")
        return
    
    download_images = not args.no_images
    
    if args.scraper == 'all':
        run_all_scrapers(args.max_results, download_images)
    else:
        db = ListingsDatabase()
        scraper_class = SCRAPERS[args.scraper]
        run_scraper(args.scraper, scraper_class, db, args.max_results, download_images)


if __name__ == '__main__':
    main()
