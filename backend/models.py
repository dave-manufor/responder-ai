"""Pydantic models for API request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class GeoJSONGeometry(BaseModel):
    """GeoJSON Point geometry."""
    type: Literal["Point"] = "Point"
    coordinates: List[float] = Field(..., description="[longitude, latitude] order")
    
    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if len(v) != 2:
            raise ValueError("Coordinates must be [longitude, latitude]")
        lon, lat = v
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return v


class HospitalProperties(BaseModel):
    """Hospital properties/metadata."""
    zone: str
    icu_capacity: int = Field(ge=0)
    trauma_capacity: int = Field(ge=0)
    specialties: List[str] = []
    contact: Optional[str] = None


class Hospital(BaseModel):
    """Hospital document model (GeoJSON Feature)."""
    id: str = Field(alias="_id")
    name: str
    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONGeometry
    properties: HospitalProperties
    allocated: int = Field(default=0, ge=0, description="Currently allocated beds")
    last_updated: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class CasualtyLog(BaseModel):
    """Individual casualty report entry."""
    timestamp: str
    transcript: str
    extracted_count: int = Field(ge=0)
    triage_color: Literal["RED", "YELLOW", "GREEN", "BLACK"]
    primary_injury: str


class Incident(BaseModel):
    """Incident session tracking model."""
    id: str = Field(alias="_id")
    status: Literal["ACTIVE", "RESOLVED", "ARCHIVED"] = "ACTIVE"
    created_at: datetime
    location: Optional[dict] = Field(default=None, description="{'lat': float, 'long': float}")
    casualty_log: List[CasualtyLog] = []
    total_casualties: int = Field(default=0, ge=0)
    allocated_beds: int = Field(default=0, ge=0)
    
    class Config:
        populate_by_name = True


class BedReservation(BaseModel):
    """Request model for bed reservation."""
    hospital_id: str
    severity: Literal["RED", "YELLOW", "GREEN", "BLACK"]
    patient_count: int = Field(default=1, ge=1, description="Number of beds to reserve")


class AllocationRequest(BaseModel):
    """Request model for bulk bed allocation."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    patient_count: int = Field(..., ge=1)
    triage_color: Literal["RED", "YELLOW", "GREEN", "BLACK"] = "RED"


class HospitalAllocation(BaseModel):
    """Single hospital allocation in a plan."""
    hospital_id: str
    hospital_name: str
    patients_sent: int
    coordinates: List[float]
    distance_km: float


class AllocationPlan(BaseModel):
    """Response model for allocation results."""
    status: Literal["SUCCESS", "PARTIAL", "OVERFLOW"]
    plan: List[HospitalAllocation]
    unallocated: int = 0
    message: Optional[str] = None


class ReservationResponse(BaseModel):
    """Response model for bed reservation."""
    status: Literal["SUCCESS", "CONFLICT"]
    hospital: Optional[str] = None
    beds_reserved: Optional[int] = None
    remaining_capacity: Optional[int] = None
    available: Optional[int] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]
    timestamp: datetime


# ============================================================================
# Phase 2 Models - Radio Transcripts and Agent Responses
# ============================================================================

class RadioTranscript(BaseModel):
    """Request model for radio transcript (text input)."""
    transcript: str = Field(..., min_length=1, description="Radio transmission text")
    session_id: Optional[str] = Field(default=None, description="Session ID for multi-turn conversation")


class TriageResult(BaseModel):
    """Triage classification result from watsonx.ai."""
    triage_color: Literal["RED", "YELLOW", "GREEN", "BLACK"]
    primary_injury: str
    specialty_needed: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent response after processing transcript."""
    session_id: str
    transcript: str
    action: Literal[
        "acknowledged",
        "location_updated",
        "casualty_reported",
        "beds_allocated",
        "triage_error",
        "allocation_error"
    ]
    message: str
    session_state: Optional[dict] = None
    triage_result: Optional[TriageResult] = None
    allocation_result: Optional[AllocationPlan] = None
