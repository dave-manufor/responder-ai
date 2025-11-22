"""Bed allocation tool for logistics - production ready."""
from typing import Dict
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ExpectedCredentials, ConnectionType
from ibm_watsonx_orchestrate.run import connections
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

# Define the App ID you will use to store the secret
DB_CONNECTION_ID = "mongodb_connection"

@tool(
    permission=ToolPermission.READ_WRITE,
    expected_credentials=[ExpectedCredentials(app_id=DB_CONNECTION_ID, type=ConnectionType.KEY_VALUE)]
)
def allocate_patient_beds_tool(
    lat: float,
    lon: float,
    patient_count: int,
    triage_color: str,
    specialty: str = None
) -> Dict:
    """Allocate trauma beds for patients at nearby hospitals.

    Performs intelligent bed allocation with atomic locking and safety buffers.

    Args:
        lat (float): Incident latitude in decimal degrees.
        lon (float): Incident longitude in decimal degrees.
        patient_count (int): Number of patients requiring beds.
        triage_color (str): START Protocol triage category (RED, YELLOW, GREEN, BLACK).
        specialty (str, optional): Required medical specialty. Defaults to None.

    Returns:
        Dict: Allocation result with status, count, and hospital plan.
    """
    # Get MongoDB connection from environment
    creds = connections.key_value(DB_CONNECTION_ID)
    # mongodb_uri = creds.get("MONGODB_URI")

    # Hard code for hackerthon
    mongodb_uri = "mongodb+srv://responder-ai:NwxHmv7xQXeQP8ew@cluster0.gtj199a.mongodb.net/retryWrites=true&w=majority"
    
    if not mongodb_uri:
        return {
            "status": "error",
            "allocated_count": 0,
            "plan": [],
            "message": "MongoDB URI not configured"
        }
    
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
        
        # Find nearby hospitals
        pipeline = [
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "distanceField": "distance",
                    "maxDistance": 10000,  # 10km
                    "spherical": True,
                    "key": "geometry"
                }
            }
        ]
        
        hospitals = list(collection.aggregate(pipeline))
        
        if not hospitals:
            client.close()
            return {
                "status": "failed",
                "allocated_count": 0,
                "plan": [],
                "message": "No hospitals found within 10km"
            }
        
        # Allocate beds
        allocation_plan = []
        remaining = patient_count
        
        for hospital in hospitals:
            if remaining <= 0:
                break
            
            total_capacity = hospital["properties"]["trauma_capacity"]
            current_allocated = hospital.get("allocated", 0)
            safe_capacity = int(total_capacity * 0.85)
            available = max(0, safe_capacity - current_allocated)
            
            if available > 0:
                allocated_here = min(available, remaining)
                
                # Lock beds
                collection.update_one(
                    {"_id": hospital["_id"]},
                    {"$inc": {"allocated": allocated_here}}
                )
                
                allocation_plan.append({
                    "hospital_name": hospital["name"],
                    "allocated_beds": allocated_here,
                    "distance_km": round(hospital.get("distance", 0) / 1000, 2)
                })
                
                remaining -= allocated_here
        
        client.close()
        
        # Determine status
        if remaining > 0:
            status = "partial" if allocation_plan else "failed"
            message = f"Allocated {patient_count - remaining}/{patient_count} patients"
        else:
            status = "success"
            message = f"Successfully allocated {patient_count} patients"
        
        return {
            "status": status,
            "allocated_count": patient_count - remaining,
            "plan": allocation_plan,
            "message": message
        }
        
    except Exception as e:
        print(f"Allocation error: {e}")
        return {
            "status": "error",
            "allocated_count": 0,
            "plan": [],
            "message": f"Error: {str(e)}"
        }
