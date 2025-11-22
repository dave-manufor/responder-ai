"""MongoDB database connection and management."""
from pymongo import MongoClient, GEOSPHERE
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import settings
from typing import Optional

# Global database connection (singleton pattern for connection pooling)
_client: Optional[MongoClient] = None
_db = None


def get_mongo_client() -> MongoClient:
    """
    Get MongoDB client instance (singleton).
    
    Returns:
        MongoClient: Thread-safe MongoDB client with connection pooling
    """
    global _client
    
    if _client is None:
        try:
            # Added tlsAllowInvalidCertificates=True to fix macOS SSL error
            _client = MongoClient(
                settings.mongodb_uri,
                server_api=ServerApi('1'),
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            # Test connection
            _client.admin.command('ping')
            print("✅ MongoDB connection established")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    return _client


def get_database():
    """
    Get database instance.
    
    Returns:
        Database: MongoDB database instance
    """
    global _db
    
    if _db is None:
        client = get_mongo_client()
        _db = client[settings.mongodb_db_name]
    
    return _db


def get_hospitals_collection():
    """Get hospitals collection with 2dsphere index."""
    db = get_database()
    collection = db.hospitals
    
    # Ensure 2dsphere index exists
    try:
        collection.create_index([("geometry", GEOSPHERE)])
    except Exception as e:
        print(f"Note: Index may already exist or creation failed: {e}")
    
    return collection


def get_incidents_collection():
    """Get incidents collection."""
    db = get_database()
    return db.incidents


def close_connection():
    """Close MongoDB connection (for cleanup)."""
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        print("MongoDB connection closed")


def check_connection() -> bool:
    """
    Check if MongoDB connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        client = get_mongo_client()
        client.admin.command('ping')
        return True
    except Exception:
        return False
