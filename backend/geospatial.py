"""Geospatial query and bed allocation logic."""
from typing import List, Dict, Optional
from database import get_hospitals_collection
from models import Hospital, HospitalAllocation, AllocationPlan


# Safety buffer constant (use only 85% of reported capacity)
SAFETY_BUFFER_PERCENT = 0.85


def find_nearby_hospitals(
    lat: float,
    lon: float,
    max_distance_km: int = 10,
    limit: int = 10
) -> List[Dict]:
    """
    Find hospitals within radius using MongoDB $geoNear aggregation.
    
    Uses $geoNear aggregation pipeline to get accurate distance calculations
    in a 'distance' field (in meters).
    
    Args:
        lat: Latitude of incident
        lon: Longitude of incident
        max_distance_km: Maximum search radius in kilometers
        limit: Maximum number of hospitals to return
    
    Returns:
        List of hospital documents sorted by distance (nearest first)
        Each document includes a 'distance' field with distance in meters
    """
    collection = get_hospitals_collection()
    
    # Use $geoNear aggregation pipeline for distance calculation
    # $geoNear must be the first stage in the pipeline
    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lon, lat]  # [LONG, LAT] order for GeoJSON!
                },
                "distanceField": "distance",  # Output field for calculated distance
                "maxDistance": max_distance_km * 1000,  # Convert km to meters
                "spherical": True,  # Use spherical geometry for Earth's surface
                "key": "geometry"  # Field to use for geospatial query
            }
        },
        {
            "$limit": limit
        }
    ]
    
    hospitals = list(collection.aggregate(pipeline))
    return hospitals


def calculate_safe_capacity(total_capacity: int, allocated: int = 0) -> int:
    """
    Calculate available safe capacity with buffer.
    
    Args:
        total_capacity: Total trauma capacity
        allocated: Currently allocated beds
    
    Returns:
        Available beds after applying safety buffer
    """
    safe_limit = int(total_capacity * SAFETY_BUFFER_PERCENT)
    available = max(0, safe_limit - allocated)
    return available


def find_and_allocate_beds(
    lat: float,
    lon: float,
    patient_count: int,
    triage_color: str = "RED"
) -> AllocationPlan:
    """
    Find nearby hospitals and allocate beds using safety buffer algorithm.
    
    This is the core allocation function that:
    1. Performs geospatial search within 10km
    2. Applies 85% safety buffer to each hospital
    3. Distributes patients across multiple hospitals if needed
    4. Locks beds by updating MongoDB
    
    Args:
        lat: Latitude of incident (-90 to 90)
        lon: Longitude of incident (-180 to 180)
        patient_count: Number of patients needing beds (must be positive)
        triage_color: Triage category (RED/YELLOW/GREEN/BLACK)
    
    Returns:
        AllocationPlan with status, plan, and unallocated count
    
    Raises:
        ValueError: If coordinates or patient count are invalid
    """
    # Validation
    if patient_count <= 0:
        raise ValueError("Patient count must be positive")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
    
    collection = get_hospitals_collection()
    
    # 1. GEOSPATIAL SEARCH: Find hospitals within 10km radius
    nearby_hospitals = find_nearby_hospitals(lat, lon, max_distance_km=10)
    
    if not nearby_hospitals:
        return AllocationPlan(
            status="OVERFLOW",
            plan=[],
            unallocated=patient_count,
            message="No hospitals found within 10km radius"
        )
    
    # 2. BULK ALLOCATION LOGIC with Safety Buffer
    allocation_plan: List[HospitalAllocation] = []
    remaining = patient_count
    
    for hospital in nearby_hospitals:
        if remaining <= 0:
            break
        
        # Get current allocation and capacity
        total_capacity = hospital["properties"]["trauma_capacity"]
        current_allocated = hospital.get("allocated", 0)
        
        # Calculate safe available capacity (85% buffer)
        available = calculate_safe_capacity(total_capacity, current_allocated)
        
        if available > 0:
            # Allocate min(available, remaining)
            allocated_here = min(available, remaining)
            
            allocation_plan.append(HospitalAllocation(
                hospital_id=hospital["_id"],
                hospital_name=hospital["name"],
                patients_sent=allocated_here,
                coordinates=hospital["geometry"]["coordinates"],
                distance_km=round(hospital.get("distance", 0) / 1000, 2)
            ))
            
            # Update database (lock beds atomically)
            collection.update_one(
                {"_id": hospital["_id"]},
                {"$inc": {"allocated": allocated_here}}
            )
            
            remaining -= allocated_here
    
    # 3. Determine final status
    if remaining > 0:
        return AllocationPlan(
            status="OVERFLOW" if not allocation_plan else "PARTIAL",
            plan=allocation_plan,
            unallocated=remaining,
            message=f"Could not allocate {remaining} patients - insufficient capacity"
        )
    
    return AllocationPlan(
        status="SUCCESS",
        plan=allocation_plan,
        unallocated=0,
        message=f"Successfully allocated {patient_count} patients across {len(allocation_plan)} hospital(s)"
    )


def reset_all_allocations() -> int:
    """
    Reset all allocated beds to 0 (for demo restarts).
    
    Returns:
        Number of hospitals updated
    """
    collection = get_hospitals_collection()
    result = collection.update_many(
        {},
        {"$set": {"allocated": 0}}
    )
    return result.modified_count
