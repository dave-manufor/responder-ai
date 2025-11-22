"""Geospatial tool for finding hospitals - production ready."""
from typing import List, Dict
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ExpectedCredentials, ConnectionType
from ibm_watsonx_orchestrate.run import connections
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

DB_CONNECTION_ID = "mongodb_connection"

@tool(
    permission=ToolPermission.READ_WRITE,
    expected_credentials=[ExpectedCredentials(app_id=DB_CONNECTION_ID, type=ConnectionType.KEY_VALUE)]
)
def find_hospitals_tool(lat: float, lon: float, max_km: int = 10) -> List[Dict]:
    """Find nearby hospitals using MongoDB geospatial queries.

    Searches for trauma-capable hospitals within a specified radius.

    Args:
        lat (float): Incident latitude in decimal degrees.
        lon (float): Incident longitude in decimal degrees.
        max_km (int): Maximum search radius in kilometers. Defaults to 10.

    Returns:
        List[Dict]: List of hospitals sorted by distance with capacity info.
    """
    # Get MongoDB connection from environment
    creds = connections.key_value(DB_CONNECTION_ID)
    # mongodb_uri = creds.get("MONGODB_URI")

    # Hard code for hackerthon
    mongodb_uri = "mongodb+srv://responder-ai:NwxHmv7xQXeQP8ew@cluster0.gtj199a.mongodb.net/retryWrites=true&w=majority"
    
    if not mongodb_uri:
        return [{
            "error": "MongoDB URI not configured",
            "name": "Configuration Error",
            "distance_km": 0,
            "available_beds": 0,
            "specialties": []
        }]
    
    try:
        # Connect to MongoDB
        client = MongoClient(
            mongodb_uri,
            server_api=ServerApi('1'),
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        db = client.respondr_hospitals
        collection = db.hospitals
        
        # Geospatial query using $geoNear
        pipeline = [
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [lon, lat]  # [LONG, LAT] for GeoJSON
                    },
                    "distanceField": "distance",
                    "maxDistance": max_km * 1000,  # km to meters
                    "spherical": True,
                    "key": "geometry"
                }
            },
            {"$limit": 10}
        ]
        
        hospitals_raw = list(collection.aggregate(pipeline))
        
        # Format results
        hospitals = []
        for h in hospitals_raw:
            safe_capacity = int(h["properties"]["trauma_capacity"] * 0.85)
            allocated = h.get("allocated", 0)
            available = max(0, safe_capacity - allocated)
            
            hospitals.append({
                "name": h["name"],
                "distance_km": round(h.get("distance", 0) / 1000, 2),
                "available_beds": available,
                "specialties": h["properties"].get("specialties", []),
                "coordinates": h["geometry"]["coordinates"]
            })
        
        client.close()
        return hospitals
        
    except Exception as e:
        print(f"Geo search error: {e}")
        return [{
            "error": str(e),
            "name": "Database Error",
            "distance_km": 0,
            "available_beds": 0,
            "specialties": []
        }]
