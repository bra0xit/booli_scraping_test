import sqlite3
import json
from datetime import datetime
import os


class BooliDatabase:
    """Database manager for Booli sold apartments"""

    def __init__(self, db_path='data/booli_sold.db'):
        """Initialize database connection"""
        self.db_path = db_path

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._create_tables()

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Booli sold apartments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS booli_sold (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booli_url TEXT UNIQUE NOT NULL,
                address TEXT,
                agent_name TEXT,
                agent_url TEXT,
                agency_name TEXT,
                agency_url TEXT,
                sold_price TEXT,
                sold_date TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def insert_apartment(self, apartment_data):
        """
        Insert or update a Booli sold apartment

        Args:
            apartment_data: Dictionary with apartment information

        Returns:
            Apartment ID (database row id)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if apartment already exists
        cursor.execute('SELECT id FROM booli_sold WHERE booli_url = ?',
                      (apartment_data['url'],))
        existing = cursor.fetchone()

        if existing:
            # Update existing apartment
            apartment_id = existing[0]

            cursor.execute('''
                UPDATE booli_sold
                SET address = ?, agent_name = ?, agent_url = ?, agency_name = ?,
                    agency_url = ?, sold_price = ?, sold_date = ?,
                    last_seen = ?, last_scraped = ?, metadata = ?
                WHERE booli_url = ?
            ''', (
                apartment_data.get('address'),
                apartment_data.get('agent'),
                apartment_data.get('agent_url'),
                apartment_data.get('agency'),
                apartment_data.get('agency_url'),
                apartment_data.get('sold_price'),
                apartment_data.get('sold_date'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps(apartment_data.get('metadata', {})),
                apartment_data['url']
            ))

            print(f"  Updated existing apartment in database")

        else:
            # Insert new apartment
            cursor.execute('''
                INSERT INTO booli_sold
                (booli_url, address, agent_name, agent_url, agency_name, agency_url,
                 sold_price, sold_date, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                apartment_data['url'],
                apartment_data.get('address'),
                apartment_data.get('agent'),
                apartment_data.get('agent_url'),
                apartment_data.get('agency'),
                apartment_data.get('agency_url'),
                apartment_data.get('sold_price'),
                apartment_data.get('sold_date'),
                json.dumps(apartment_data.get('metadata', {}))
            ))

            apartment_id = cursor.lastrowid
            print(f"  Inserted new apartment to database")

        conn.commit()
        conn.close()

        return apartment_id

    def get_apartments(self, limit=None):
        """
        Get apartments from database

        Args:
            limit: Maximum number of results

        Returns:
            List of apartment dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM booli_sold ORDER BY last_scraped DESC'

        if limit:
            query += ' LIMIT ?'
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        apartments = []
        for row in rows:
            apartment = dict(row)

            # Parse metadata JSON
            if apartment['metadata']:
                try:
                    apartment['metadata'] = json.loads(apartment['metadata'])
                except:
                    apartment['metadata'] = {}

            apartments.append(apartment)

        conn.close()
        return apartments

    def get_apartment_by_url(self, url):
        """Get a single apartment by Booli URL"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM booli_sold WHERE booli_url = ?', (url,))
        row = cursor.fetchone()

        if row:
            apartment = dict(row)
            if apartment['metadata']:
                try:
                    apartment['metadata'] = json.loads(apartment['metadata'])
                except:
                    apartment['metadata'] = {}
            conn.close()
            return apartment

        conn.close()
        return None

    def get_stats(self):
        """Get database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total apartments
        cursor.execute('SELECT COUNT(*) FROM booli_sold')
        stats['total_apartments'] = cursor.fetchone()[0]

        # Apartments by agent
        cursor.execute('''
            SELECT agent_name, COUNT(*) as count
            FROM booli_sold
            WHERE agent_name IS NOT NULL
            GROUP BY agent_name
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['top_agents'] = [{'agent': row[0], 'count': row[1]} for row in cursor.fetchall()]

        # Apartments by agency
        cursor.execute('''
            SELECT agency_name, COUNT(*) as count
            FROM booli_sold
            WHERE agency_name IS NOT NULL
            GROUP BY agency_name
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['top_agencies'] = [{'agency': row[0], 'count': row[1]} for row in cursor.fetchall()]

        conn.close()
        return stats


class HemnetDatabase:
    """Database manager for Hemnet listings"""

    def __init__(self, db_path='data/hemnet_listings.db'):
        """Initialize database connection"""
        self.db_path = db_path

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._create_tables()

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Hemnet listings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hemnet_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hemnet_id TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                address TEXT NOT NULL,
                area TEXT,
                asking_price INTEGER,
                monthly_fee INTEGER,
                rooms REAL,
                size_sqm REAL,
                floor TEXT,
                build_year INTEGER,
                property_type TEXT,
                agent_name TEXT,
                agency_name TEXT,
                listing_date TEXT,
                description TEXT,
                status TEXT DEFAULT 'active',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')

        # Images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listing_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                local_path TEXT,
                image_order INTEGER,
                downloaded BOOLEAN DEFAULT 0,
                download_date TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES hemnet_listings(id)
            )
        ''')

        # Price history table (for tracking price changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                price INTEGER NOT NULL,
                changed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES hemnet_listings(id)
            )
        ''')

        conn.commit()
        conn.close()

    def insert_listing(self, listing_data):
        """
        Insert or update a Hemnet listing

        Args:
            listing_data: Dictionary with listing information

        Returns:
            Listing ID (database row id)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if listing already exists
        cursor.execute('SELECT id, asking_price FROM hemnet_listings WHERE hemnet_id = ?',
                      (listing_data['hemnet_id'],))
        existing = cursor.fetchone()

        if existing:
            # Update existing listing
            listing_id = existing[0]
            old_price = existing[1]

            cursor.execute('''
                UPDATE hemnet_listings
                SET url = ?, address = ?, area = ?, asking_price = ?, monthly_fee = ?,
                    rooms = ?, size_sqm = ?, floor = ?, build_year = ?, property_type = ?,
                    agent_name = ?, agency_name = ?, listing_date = ?, description = ?,
                    status = ?, last_seen = ?, last_scraped = ?, metadata = ?
                WHERE hemnet_id = ?
            ''', (
                listing_data.get('url'),
                listing_data.get('address'),
                listing_data.get('area'),
                listing_data.get('asking_price'),
                listing_data.get('monthly_fee'),
                listing_data.get('rooms'),
                listing_data.get('size_sqm'),
                listing_data.get('floor'),
                listing_data.get('build_year'),
                listing_data.get('property_type'),
                listing_data.get('agent_name'),
                listing_data.get('agency_name'),
                listing_data.get('listing_date'),
                listing_data.get('description'),
                listing_data.get('status', 'active'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps(listing_data.get('metadata', {})),
                listing_data['hemnet_id']
            ))

            # Track price change if price is different
            new_price = listing_data.get('asking_price')
            if new_price and old_price and new_price != old_price:
                cursor.execute('''
                    INSERT INTO price_history (listing_id, price)
                    VALUES (?, ?)
                ''', (listing_id, new_price))
                print(f"  Price changed: {old_price} -> {new_price} SEK")

        else:
            # Insert new listing
            cursor.execute('''
                INSERT INTO hemnet_listings
                (hemnet_id, url, address, area, asking_price, monthly_fee, rooms, size_sqm,
                 floor, build_year, property_type, agent_name, agency_name, listing_date,
                 description, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                listing_data['hemnet_id'],
                listing_data.get('url'),
                listing_data.get('address'),
                listing_data.get('area'),
                listing_data.get('asking_price'),
                listing_data.get('monthly_fee'),
                listing_data.get('rooms'),
                listing_data.get('size_sqm'),
                listing_data.get('floor'),
                listing_data.get('build_year'),
                listing_data.get('property_type'),
                listing_data.get('agent_name'),
                listing_data.get('agency_name'),
                listing_data.get('listing_date'),
                listing_data.get('description'),
                listing_data.get('status', 'active'),
                json.dumps(listing_data.get('metadata', {}))
            ))

            listing_id = cursor.lastrowid

            # Record initial price
            if listing_data.get('asking_price'):
                cursor.execute('''
                    INSERT INTO price_history (listing_id, price)
                    VALUES (?, ?)
                ''', (listing_id, listing_data['asking_price']))

        conn.commit()
        conn.close()

        return listing_id

    def insert_images(self, listing_id, image_urls):
        """
        Insert image URLs for a listing

        Args:
            listing_id: Database listing ID
            image_urls: List of image URLs
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete existing images for this listing (in case of re-scrape)
        cursor.execute('DELETE FROM listing_images WHERE listing_id = ?', (listing_id,))

        # Insert new images
        for idx, url in enumerate(image_urls):
            cursor.execute('''
                INSERT INTO listing_images (listing_id, image_url, image_order)
                VALUES (?, ?, ?)
            ''', (listing_id, url, idx))

        conn.commit()
        conn.close()

    def update_image_path(self, image_id, local_path):
        """Update local path for downloaded image"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE listing_images
            SET local_path = ?, downloaded = 1, download_date = ?
            WHERE id = ?
        ''', (local_path, datetime.now().isoformat(), image_id))

        conn.commit()
        conn.close()

    def get_listings(self, status='active', limit=None):
        """
        Get listings from database

        Args:
            status: Filter by status (active, sold, removed, all)
            limit: Maximum number of results

        Returns:
            List of listing dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM hemnet_listings'
        params = []

        if status != 'all':
            query += ' WHERE status = ?'
            params.append(status)

        query += ' ORDER BY last_scraped DESC'

        if limit:
            query += ' LIMIT ?'
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        listings = []
        for row in rows:
            listing = dict(row)

            # Parse metadata JSON
            if listing['metadata']:
                listing['metadata'] = json.loads(listing['metadata'])

            # Get images for this listing
            cursor.execute('''
                SELECT image_url, local_path, image_order, downloaded
                FROM listing_images
                WHERE listing_id = ?
                ORDER BY image_order
            ''', (listing['id'],))

            images = []
            for img_row in cursor.fetchall():
                images.append({
                    'url': img_row[0],
                    'local_path': img_row[1],
                    'order': img_row[2],
                    'downloaded': bool(img_row[3])
                })

            listing['images'] = images
            listings.append(listing)

        conn.close()
        return listings

    def get_listing_by_id(self, listing_id):
        """Get a single listing by database ID"""
        listings = self.get_listings(status='all')
        for listing in listings:
            if listing['id'] == listing_id:
                return listing
        return None

    def get_listing_by_hemnet_id(self, hemnet_id):
        """Get a single listing by Hemnet ID"""
        listings = self.get_listings(status='all')
        for listing in listings:
            if listing['hemnet_id'] == hemnet_id:
                return listing
        return None

    def mark_listing_status(self, hemnet_id, status):
        """Update listing status (active, sold, removed)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE hemnet_listings
            SET status = ?, last_seen = ?
            WHERE hemnet_id = ?
        ''', (status, datetime.now().isoformat(), hemnet_id))

        conn.commit()
        conn.close()

    def get_stats(self):
        """Get database statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Count listings by status
        cursor.execute('SELECT status, COUNT(*) FROM hemnet_listings GROUP BY status')
        stats['by_status'] = dict(cursor.fetchall())

        # Total listings
        cursor.execute('SELECT COUNT(*) FROM hemnet_listings')
        stats['total_listings'] = cursor.fetchone()[0]

        # Total images
        cursor.execute('SELECT COUNT(*) FROM listing_images')
        stats['total_images'] = cursor.fetchone()[0]

        # Downloaded images
        cursor.execute('SELECT COUNT(*) FROM listing_images WHERE downloaded = 1')
        stats['downloaded_images'] = cursor.fetchone()[0]

        conn.close()
        return stats
