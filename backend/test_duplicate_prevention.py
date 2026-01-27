#!/usr/bin/env python3
"""Test script to verify Booli duplicate prevention"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from storage.database import BooliDatabase

def test_duplicate_prevention():
    """Test that the database prevents duplicates"""

    # Initialize database
    db = BooliDatabase(db_path='data/test_booli.db')

    print("Testing Booli duplicate prevention...")
    print("=" * 50)

    # Test apartment data
    apartment1 = {
        'url': 'https://www.booli.se/annons/test-123',
        'address': 'Test Street 123, Stockholm',
        'agent': 'Test Agent',
        'agent_url': 'https://example.com/agent/1',
        'agency': 'Test Agency',
        'agency_url': 'https://example.com/agency/1',
        'sold_price': '8 500 000 kr',
        'sold_date': '2024-01-15',
        'metadata': {'test': True}
    }

    # Insert first time
    print("\n1. First insert (should create new record):")
    id1 = db.insert_apartment(apartment1)
    print(f"   Result: Created apartment with ID {id1}")

    # Check stats
    stats = db.get_stats()
    print(f"   Total apartments in DB: {stats['total_apartments']}")

    # Try to insert same apartment again (should update, not create duplicate)
    print("\n2. Second insert with same URL (should update existing):")
    apartment1_updated = apartment1.copy()
    apartment1_updated['sold_price'] = '8 600 000 kr'  # Changed price
    id2 = db.insert_apartment(apartment1_updated)
    print(f"   Result: Returned ID {id2}")

    # Check stats again
    stats = db.get_stats()
    print(f"   Total apartments in DB: {stats['total_apartments']}")

    if stats['total_apartments'] == 1:
        print("\n✅ SUCCESS: No duplicate created! Database has exactly 1 apartment.")
    else:
        print(f"\n❌ FAILURE: Expected 1 apartment, but found {stats['total_apartments']}")
        return False

    # Verify the apartment was updated
    print("\n3. Verify data was updated:")
    saved = db.get_apartment_by_url('https://www.booli.se/annons/test-123')
    if saved:
        print(f"   Address: {saved['address']}")
        print(f"   Sold Price: {saved['sold_price']}")
        if saved['sold_price'] == '8 600 000 kr':
            print("   ✅ Price was updated correctly!")
        else:
            print(f"   ❌ Price not updated. Expected '8 600 000 kr', got '{saved['sold_price']}'")

    # Insert different apartment
    print("\n4. Insert different apartment (should create new record):")
    apartment2 = {
        'url': 'https://www.booli.se/annons/test-456',
        'address': 'Different Street 456, Stockholm',
        'agent': 'Another Agent',
        'agent_url': 'https://example.com/agent/2',
        'agency': 'Another Agency',
        'agency_url': 'https://example.com/agency/2',
        'sold_price': '9 200 000 kr',
        'sold_date': '2024-02-20',
        'metadata': {'test': True}
    }
    id3 = db.insert_apartment(apartment2)
    print(f"   Result: Created apartment with ID {id3}")

    # Final stats
    stats = db.get_stats()
    print(f"\n5. Final count: {stats['total_apartments']} apartments")

    if stats['total_apartments'] == 2:
        print("   ✅ Correct! We now have 2 different apartments.")
    else:
        print(f"   ❌ Expected 2 apartments, got {stats['total_apartments']}")
        return False

    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED - Duplicate prevention works!")
    print("=" * 50)

    # Clean up test database
    import os
    if os.path.exists('data/test_booli.db'):
        os.remove('data/test_booli.db')
        print("\nTest database cleaned up.")

    return True

if __name__ == '__main__':
    success = test_duplicate_prevention()
    sys.exit(0 if success else 1)
