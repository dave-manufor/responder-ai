"""
Comprehensive unit tests for Respondr.ai FastAPI endpoints.

Tests cover:
- Health check endpoint
- Hospital listing (all and geospatial)
- Bed reservation with safety buffer
- Bulk allocation algorithm
- Reset functionality
- Edge cases and validation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from main import app
from models import Hospital, AllocationPlan, HospitalAllocation

# Test client
client = TestClient(app)


# ============================================================================
# FIXTURES - Mock Data
# ============================================================================

@pytest.fixture
def mock_hospital_data():
    """Sample hospital documents."""
    return [
        {
            "_id": "hosp_001",
            "name": "Kenyatta National Hospital",
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [36.8219, -1.2921]
            },
            "properties": {
                "zone": "Upper Hill",
                "icu_capacity": 20,
                "trauma_capacity": 15,
                "specialties": ["Trauma", "Neurosurgery"],
                "contact": "+254-XXX-1111"
            },
            "allocated": 0,
            "distance": 2300  # 2.3km in meters
        },
        {
            "_id": "hosp_002",
            "name": "Nairobi Hospital",
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [36.8120, -1.2850]
            },
            "properties": {
                "zone": "Parklands",
                "icu_capacity": 10,
                "trauma_capacity": 8,
                "specialties": ["General Surgery"],
                "contact": "+254-XXX-2222"
            },
            "allocated": 0,
            "distance": 4100  # 4.1km
        },
        {
            "_id": "hosp_003",
            "name": "Aga Khan Hospital",
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [36.8000, -1.2800]
            },
            "properties": {
                "zone": "Central",
                "icu_capacity": 12,
                "trauma_capacity": 10,
                "specialties": ["Cardiology", "Trauma"],
                "contact": "+254-XXX-3333"
            },
            "allocated": 5,  # Already has some allocations
            "distance": 6500  # 6.5km
        }
    ]


@pytest.fixture
def mock_db_collection(mock_hospital_data):
    """Mock MongoDB collection."""
    collection = MagicMock()
    collection.find = MagicMock(return_value=mock_hospital_data)
    collection.find_one = MagicMock(return_value=mock_hospital_data[0])
    collection.update_one = MagicMock(return_value=MagicMock(modified_count=1))
    collection.update_many = MagicMock(return_value=MagicMock(modified_count=3))
    return collection


# ============================================================================
# TEST: Health Check
# ============================================================================

@patch('main.check_connection')
def test_health_check_healthy(mock_check):
    """Test health endpoint when database is connected."""
    mock_check.return_value = True
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


@patch('main.check_connection')
def test_health_check_unhealthy(mock_check):
    """Test health endpoint when database is disconnected."""
    mock_check.return_value = False
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "disconnected"


# ============================================================================
# TEST: List Hospitals
# ============================================================================

@patch('main.get_hospitals_collection')
def test_list_all_hospitals(mock_get_collection, mock_db_collection, mock_hospital_data):
    """Test listing all hospitals without filters."""
    mock_get_collection.return_value = mock_db_collection
    mock_db_collection.find.return_value = mock_hospital_data
    
    response = client.get("/hospitals")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Kenyatta National Hospital"
    assert data[0]["_id"] == "hosp_001"


@patch('main.find_nearby_hospitals')
@patch('main.get_hospitals_collection')
def test_list_hospitals_geospatial(mock_get_collection, mock_find_nearby, mock_hospital_data):
    """Test listing hospitals with geospatial proximity filter."""
    mock_get_collection.return_value = MagicMock()
    mock_find_nearby.return_value = mock_hospital_data[:2]  # Return closest 2
    
    response = client.get("/hospitals?lat=-1.2921&lon=36.8219&max_km=5")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Verify find_nearby_hospitals was called with correct params
    mock_find_nearby.assert_called_once_with(-1.2921, 36.8219, 5)


# ============================================================================
# TEST: Reserve Bed - Success Cases
# ============================================================================

@patch('main.get_hospitals_collection')
def test_reserve_bed_success(mock_get_collection, mock_db_collection, mock_hospital_data):
    """Test successful bed reservation."""
    mock_get_collection.return_value = mock_db_collection
    mock_db_collection.find_one.return_value = mock_hospital_data[0]
    
    response = client.post("/reserve_bed", json={
        "hospital_id": "hosp_001",
        "severity": "RED",
        "patient_count": 2
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["beds_reserved"] == 2
    assert data["hospital"] == "Kenyatta National Hospital"
    assert "remaining_capacity" in data
    
    # Verify database update was called
    mock_db_collection.update_one.assert_called_once()


@patch('main.get_hospitals_collection')
def test_reserve_bed_single_default(mock_get_collection, mock_db_collection, mock_hospital_data):
    """Test reserving single bed (default patient_count)."""
    mock_get_collection.return_value = mock_db_collection
    mock_db_collection.find_one.return_value = mock_hospital_data[0]
    
    response = client.post("/reserve_bed", json={
        "hospital_id": "hosp_001",
        "severity": "YELLOW"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["beds_reserved"] == 1


# ============================================================================
# TEST: Reserve Bed - Conflict Cases
# ============================================================================

@patch('main.get_hospitals_collection')
def test_reserve_bed_buffer_limit(mock_get_collection, mock_db_collection, mock_hospital_data):
    """Test reservation hitting safety buffer limit."""
    mock_get_collection.return_value = mock_db_collection
    
    # Hospital with 15 capacity, 85% = 12 safe, already allocated 10
    hospital = mock_hospital_data[0].copy()
    hospital["allocated"] = 10
    mock_db_collection.find_one.return_value = hospital
    
    # Try to reserve 5 beds (only 2 available after buffer)
    response = client.post("/reserve_bed", json={
        "hospital_id": "hosp_001",
        "severity": "RED",
        "patient_count": 5
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFLICT"
    assert data["available"] == 2
    assert "Ghost Capacity protection" in data["message"]
    
    # Verify NO database update occurred
    mock_db_collection.update_one.assert_not_called()


@patch('main.get_hospitals_collection')
def test_reserve_bed_hospital_not_found(mock_get_collection, mock_db_collection):
    """Test reservation for non-existent hospital."""
    mock_get_collection.return_value = mock_db_collection
    mock_db_collection.find_one.return_value = None
    
    response = client.post("/reserve_bed", json={
        "hospital_id": "hosp_999",
        "severity": "RED",
        "patient_count": 1
    })
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ============================================================================
# TEST: Allocate Beds - Success Cases
# ============================================================================

@patch('main.find_and_allocate_beds')
def test_allocate_beds_success(mock_allocate):
    """Test successful bulk allocation."""
    mock_allocate.return_value = AllocationPlan(
        status="SUCCESS",
        plan=[
            HospitalAllocation(
                hospital_id="hosp_001",
                hospital_name="Kenyatta National Hospital",
                patients_sent=12,
                coordinates=[36.8219, -1.2921],
                distance_km=2.3
            ),
            HospitalAllocation(
                hospital_id="hosp_002",
                hospital_name="Nairobi Hospital",
                patients_sent=8,
                coordinates=[36.8120, -1.2850],
                distance_km=4.1
            )
        ],
        unallocated=0,
        message="Successfully allocated 20 patients across 2 hospital(s)"
    )
    
    response = client.post("/api/allocate", json={
        "lat": -1.2921,
        "lon": 36.8219,
        "patient_count": 20,
        "triage_color": "RED"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert len(data["plan"]) == 2
    assert data["unallocated"] == 0
    assert data["plan"][0]["patients_sent"] == 12
    assert data["plan"][1]["patients_sent"] == 8
    
    # Verify function called with correct args
    mock_allocate.assert_called_once_with(
        lat=-1.2921,
        lon=36.8219,
        patient_count=20,
        triage_color="RED"
    )


@patch('main.find_and_allocate_beds')
def test_allocate_beds_partial(mock_allocate):
    """Test partial allocation when capacity is insufficient."""
    mock_allocate.return_value = AllocationPlan(
        status="PARTIAL",
        plan=[
            HospitalAllocation(
                hospital_id="hosp_001",
                hospital_name="Hospital A",
                patients_sent=10,
                coordinates=[36.82, -1.29],
                distance_km=2.0
            )
        ],
        unallocated=10,
        message="Could not allocate 10 patients - insufficient capacity"
    )
    
    response = client.post("/api/allocate", json={
        "lat": -1.29,
        "lon": 36.82,
        "patient_count": 20,
        "triage_color": "YELLOW"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PARTIAL"
    assert data["unallocated"] == 10
    assert len(data["plan"]) == 1


@patch('main.find_and_allocate_beds')
def test_allocate_beds_overflow(mock_allocate):
    """Test overflow when no hospitals can accommodate."""
    mock_allocate.return_value = AllocationPlan(
        status="OVERFLOW",
        plan=[],
        unallocated=50,
        message="No hospitals found within 10km radius"
    )
    
    response = client.post("/api/allocate", json={
        "lat": -1.5,
        "lon": 36.5,
        "patient_count": 50,
        "triage_color": "RED"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OVERFLOW"
    assert data["unallocated"] == 50
    assert len(data["plan"]) == 0


# ============================================================================
# TEST: Allocate Beds - Validation
# ============================================================================

@patch('main.find_and_allocate_beds')
def test_allocate_invalid_coordinates(mock_allocate):
    """Test allocation with invalid coordinates."""
    mock_allocate.side_effect = ValueError("Latitude must be between -90 and 90")
    
    response = client.post("/api/allocate", json={
        "lat": 100,  # Invalid
        "lon": 36.82,
        "patient_count": 10,
        "triage_color": "RED"
    })
    
    assert response.status_code == 400
    assert "Latitude" in response.json()["detail"]


def test_allocate_invalid_patient_count():
    """Test allocation with invalid patient count (Pydantic validation)."""
    response = client.post("/api/allocate", json={
        "lat": -1.29,
        "lon": 36.82,
        "patient_count": 0,  # Must be >= 1
        "triage_color": "RED"
    })
    
    assert response.status_code == 422  # Pydantic validation error


def test_allocate_invalid_triage_color():
    """Test allocation with invalid triage color."""
    response = client.post("/api/allocate", json={
        "lat": -1.29,
        "lon": 36.82,
        "patient_count": 10,
        "triage_color": "PURPLE"  # Invalid, must be RED/YELLOW/GREEN/BLACK
    })
    
    assert response.status_code == 422


# ============================================================================
# TEST: Reset Allocations
# ============================================================================

@patch('main.reset_all_allocations')
def test_reset_allocations(mock_reset):
    """Test resetting all allocated beds."""
    mock_reset.return_value = 5  # 5 hospitals updated
    
    response = client.post("/api/reset")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "5 hospital(s) updated" in data["message"]
    mock_reset.assert_called_once()


# ============================================================================
# TEST: Root Endpoint
# ============================================================================

def test_root_endpoint():
    """Test root endpoint returns service info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "endpoints" in data
    assert data["status"] == "operational"


# ============================================================================
# TEST: Request Validation
# ============================================================================

def test_reserve_bed_missing_fields():
    """Test bed reservation with missing required fields."""
    response = client.post("/reserve_bed", json={
        "severity": "RED"
        # Missing hospital_id
    })
    
    assert response.status_code == 422


def test_reserve_bed_invalid_severity():
    """Test bed reservation with invalid severity."""
    response = client.post("/reserve_bed", json={
        "hospital_id": "hosp_001",
        "severity": "ORANGE",  # Invalid
        "patient_count": 1
    })
    
    assert response.status_code == 422


def test_allocate_missing_coordinates():
    """Test allocation with missing coordinates."""
    response = client.post("/api/allocate", json={
        "patient_count": 10,
        "triage_color": "RED"
        # Missing lat/lon
    })
    
    assert response.status_code == 422


# ============================================================================
# EDGE CASES
# ============================================================================

@patch('main.get_hospitals_collection')
def test_reserve_bed_exactly_at_buffer_limit(mock_get_collection, mock_db_collection, mock_hospital_data):
    """Test reservation exactly at 85% buffer limit."""
    mock_get_collection.return_value = mock_db_collection
    
    # Hospital: 15 capacity, 85% = 12, allocated 11
    hospital = mock_hospital_data[0].copy()
    hospital["allocated"] = 11
    mock_db_collection.find_one.return_value = hospital
    
    # Request exactly 1 bed (the last available)
    response = client.post("/reserve_bed", json={
        "hospital_id": "hosp_001",
        "severity": "RED",
        "patient_count": 1
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["remaining_capacity"] == 0


@patch('main.find_and_allocate_beds')
def test_allocate_single_patient(mock_allocate):
    """Test allocating single patient."""
    mock_allocate.return_value = AllocationPlan(
        status="SUCCESS",
        plan=[
            HospitalAllocation(
                hospital_id="hosp_001",
                hospital_name="Test Hospital",
                patients_sent=1,
                coordinates=[36.82, -1.29],
                distance_km=1.5
            )
        ],
        unallocated=0
    )
    
    response = client.post("/api/allocate", json={
        "lat": -1.29,
        "lon": 36.82,
        "patient_count": 1,
        "triage_color": "GREEN"
    })
    
    assert response.status_code == 200
    assert response.json()["plan"][0]["patients_sent"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
