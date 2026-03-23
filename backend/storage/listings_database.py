"""
Unified database for all realtor listings
Stores listings from multiple sources with deduplication
"""

import sqlite3
import json
from datetime import datetime
import os
from typing import List, Dict, Any, Optional


class ListingsDatabase:
    """Unified database for listings from all realtors"""

    def __init__(self, db_path='data/all_listings.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Create database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Main listings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT NOT NULL,
                url TEXT NOT NULL,
                address TEXT,
                area TEXT,
                city TEXT DEFAULT 'Stockholm',
                asking_price INTEGER,
                monthly_fee INTEGER,
                rooms REAL,
                size_sqm REAL,
                floor TEXT,
                build_year INTEGER,
                property_type TEXT,
                agent_name TEXT,
                agent_phone TEXT,
                agent_email TEXT,
                agency_name TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                UNIQUE(source, source_id)
            )
        ''')

        # Images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listing_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                local_path TEXT,
                image_order INTEGER DEFAULT 0,
                downloaded BOOLEAN DEFAULT 0,
                download_date TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings(id),
                UNIQUE(listing_id, image_url)
            )
        ''')

        # Scrape runs log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                listings_found INTEGER DEFAULT 0,
                listings_new INTEGER DEFAULT 0,
                listings_updated INTEGER DEFAULT 0,
                images_downloaded INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error_message TEXT
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_source ON listings(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_address ON listings(address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(asking_price)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_listing ON listing_images(listing_id)')

        conn.commit()
        conn.close()

    def start_scrape_run(self, source: str) -> int:
        """Start a new scrape run and return its ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO scrape_runs (source) VALUES (?)',
            (source,)
        )
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return run_id

    def finish_scrape_run(self, run_id: int, stats: Dict[str, Any], error: str = None):
        """Complete a scrape run with stats"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE scrape_runs SET
                completed_at = ?,
                listings_found = ?,
                listings_new = ?,
                listings_updated = ?,
                images_downloaded = ?,
                status = ?,
                error_message = ?
            WHERE id = ?
        ''', (
            datetime.now().isoformat(),
            stats.get('found', 0),
            stats.get('new', 0),
            stats.get('updated', 0),
            stats.get('images', 0),
            'error' if error else 'completed',
            error,
            run_id
        ))
        conn.commit()
        conn.close()

    def upsert_listing(self, listing_data: Dict[str, Any]) -> tuple:
        """
        Insert or update a listing.
        Returns (listing_id, is_new)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        source = listing_data.get('source')
        source_id = listing_data.get('source_id')

        # Check if exists
        cursor.execute(
            'SELECT id FROM listings WHERE source = ? AND source_id = ?',
            (source, source_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing
            listing_id = existing[0]
            cursor.execute('''
                UPDATE listings SET
                    url = ?, address = ?, area = ?, city = ?,
                    asking_price = ?, monthly_fee = ?, rooms = ?, size_sqm = ?,
                    floor = ?, build_year = ?, property_type = ?,
                    agent_name = ?, agent_phone = ?, agent_email = ?, agency_name = ?,
                    description = ?, last_seen = ?, last_scraped = ?, metadata = ?
                WHERE id = ?
            ''', (
                listing_data.get('url'),
                listing_data.get('address'),
                listing_data.get('area'),
                listing_data.get('city', 'Stockholm'),
                listing_data.get('asking_price'),
                listing_data.get('monthly_fee'),
                listing_data.get('rooms'),
                listing_data.get('size_sqm'),
                listing_data.get('floor'),
                listing_data.get('build_year'),
                listing_data.get('property_type'),
                listing_data.get('agent_name'),
                listing_data.get('agent_phone'),
                listing_data.get('agent_email'),
                listing_data.get('agency_name'),
                listing_data.get('description'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps(listing_data.get('raw_data'), ensure_ascii=False) if listing_data.get('raw_data') else None,
                listing_id
            ))
            is_new = False
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO listings (
                    source, source_id, url, address, area, city,
                    asking_price, monthly_fee, rooms, size_sqm,
                    floor, build_year, property_type,
                    agent_name, agent_phone, agent_email, agency_name,
                    description, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source,
                source_id,
                listing_data.get('url'),
                listing_data.get('address'),
                listing_data.get('area'),
                listing_data.get('city', 'Stockholm'),
                listing_data.get('asking_price'),
                listing_data.get('monthly_fee'),
                listing_data.get('rooms'),
                listing_data.get('size_sqm'),
                listing_data.get('floor'),
                listing_data.get('build_year'),
                listing_data.get('property_type'),
                listing_data.get('agent_name'),
                listing_data.get('agent_phone'),
                listing_data.get('agent_email'),
                listing_data.get('agency_name'),
                listing_data.get('description'),
                json.dumps(listing_data.get('raw_data'), ensure_ascii=False) if listing_data.get('raw_data') else None
            ))
            listing_id = cursor.lastrowid
            is_new = True

        conn.commit()
        conn.close()
        return listing_id, is_new

    def add_images(self, listing_id: int, image_urls: List[str], local_paths: List[str] = None):
        """Add images for a listing"""
        conn = self._get_connection()
        cursor = conn.cursor()

        local_paths = local_paths or [None] * len(image_urls)

        for i, (url, local_path) in enumerate(zip(image_urls, local_paths)):
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO listing_images 
                    (listing_id, image_url, local_path, image_order, downloaded, download_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    listing_id,
                    url,
                    local_path,
                    i,
                    1 if local_path else 0,
                    datetime.now().isoformat() if local_path else None
                ))
            except Exception as e:
                print(f"Error adding image: {e}")

        conn.commit()
        conn.close()

    def get_listings(self, source: str = None, status: str = 'active', 
                     limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get listings with optional filters"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM listings WHERE 1=1'
        params = []

        if source:
            query += ' AND source = ?'
            params.append(source)
        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY last_seen DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_listing_images(self, listing_id: int) -> List[Dict]:
        """Get images for a listing"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM listing_images 
            WHERE listing_id = ? 
            ORDER BY image_order
        ''', (listing_id,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total listings by source
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM listings 
            GROUP BY source
        ''')
        stats['by_source'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Total active listings
        cursor.execute('SELECT COUNT(*) FROM listings WHERE status = "active"')
        stats['active_listings'] = cursor.fetchone()[0]

        # Total images
        cursor.execute('SELECT COUNT(*) FROM listing_images WHERE downloaded = 1')
        stats['downloaded_images'] = cursor.fetchone()[0]

        # Recent scrape runs
        cursor.execute('''
            SELECT source, started_at, status, listings_new 
            FROM scrape_runs 
            ORDER BY started_at DESC 
            LIMIT 10
        ''')
        stats['recent_runs'] = [
            {'source': r[0], 'started_at': r[1], 'status': r[2], 'new': r[3]}
            for r in cursor.fetchall()
        ]

        conn.close()
        return stats

    def mark_inactive(self, source: str, active_ids: List[str]):
        """Mark listings not in active_ids as inactive"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if active_ids:
            placeholders = ','.join('?' * len(active_ids))
            cursor.execute(f'''
                UPDATE listings 
                SET status = 'inactive' 
                WHERE source = ? AND source_id NOT IN ({placeholders})
            ''', [source] + active_ids)
        else:
            cursor.execute('''
                UPDATE listings SET status = 'inactive' WHERE source = ?
            ''', (source,))

        conn.commit()
        conn.close()
