"""Seed script to populate MongoDB with hospital data."""
import json
from pathlib import Path
from pymongo import GEOSPHERE
from database import get_database, get_hospitals_collection


def load_hospital_data():
    """Load hospital data from JSON file."""
    json_path = Path(__file__).parent / "hospitals.json"
    
    with open(json_path, 'r') as f:
        return json.load(f)


def seed_hospitals():
    """Populate MongoDB with hospital data and create geospatial index."""
    print("🏥 Seeding hospital data...")
    
    try:
        collection = get_hospitals_collection()
        
        # Load data
        hospitals = load_hospital_data()
        print(f"📄 Loaded {len(hospitals)} hospitals from hospitals.json")
        
        # Clear existing data
        result = collection.delete_many({})
        print(f"🗑️  Deleted {result.deleted_count} existing records")
        
        # Insert new data
        result = collection.insert_many(hospitals)
        print(f"✅ Inserted {len(result.inserted_ids)} hospitals")
        
        # Create 2dsphere index (if not exists)
        try:
            collection.create_index([("geometry", GEOSPHERE)])
            print("🌍 Created 2dsphere geospatial index on 'geometry' field")
        except Exception as e:
            print(f"ℹ️  Index creation note: {e}")
        
        # Verify data
        count = collection.count_documents({})
        print(f"✅ Verification: {count} hospitals in database")
        
        # Show sample
        sample = collection.find_one({})
        if sample:
            print(f"\n📍 Sample hospital:")
            print(f"   Name: {sample['name']}")
            print(f"   Coordinates: {sample['geometry']['coordinates']}")
            print(f"   Trauma Capacity: {sample['properties']['trauma_capacity']}")
        
        print("\n🎉 Seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise


if __name__ == "__main__":
    seed_hospitals()
