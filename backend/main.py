"""FastAPI application - Respondr.ai backend."""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional

from config import settings
from database import get_hospitals_collection, check_connection
from models import (
    Hospital,
    BedReservation,
    ReservationResponse,
    AllocationRequest,
    AllocationPlan,
    HealthResponse,
    RadioTranscript,
    AgentResponse
)
from geospatial import (
    find_nearby_hospitals,
    find_and_allocate_beds,
    calculate_safe_capacity,
    reset_all_allocations
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Mass Casualty Triage & Logistics Assistant API"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns database connection status and timestamp.
    """
    db_healthy = check_connection()
    
    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        database="connected" if db_healthy else "disconnected",
        timestamp=datetime.utcnow()
    )


@app.get("/hospitals", response_model=List[dict])
async def list_hospitals(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    max_km: int = 10
):
    """
    List all hospitals or filter by proximity.
    
    Query Parameters:
        lat: Latitude for proximity search
        lon: Longitude for proximity search
        max_km: Maximum distance in kilometers (default: 10)
    
    Returns:
        List of hospitals (sorted by distance if lat/lon provided)
    """
    collection = get_hospitals_collection()
    
    # If coordinates provided, use geospatial query
    if lat is not None and lon is not None:
        hospitals = find_nearby_hospitals(lat, lon, max_km)
    else:
        # Return all hospitals
        hospitals = list(collection.find({}))
    
    # Convert ObjectId to string for JSON serialization
    for h in hospitals:
        h["_id"] = str(h["_id"])
    
    return hospitals


@app.post("/reserve_bed", response_model=ReservationResponse)
async def reserve_bed(reservation: BedReservation):
    """
    Reserve bed(s) at a specific hospital with safety buffer logic.
    
    Request Body:
        hospital_id: Hospital identifier
        severity: Triage color (RED/YELLOW/GREEN/BLACK)
        patient_count: Number of beds to reserve (default: 1)
    
    Returns:
        Reservation status with remaining capacity or conflict message
    """
    collection = get_hospitals_collection()
    
    # Find hospital
    hospital = collection.find_one({"_id": reservation.hospital_id})
    
    if not hospital:
        raise HTTPException(status_code=404, detail=f"Hospital '{reservation.hospital_id}' not found")
    
    # Calculate safe capacity with buffer
    total_capacity = hospital["properties"]["trauma_capacity"]
    current_allocated = hospital.get("allocated", 0)
    available = calculate_safe_capacity(total_capacity, current_allocated)
    
    # Check if we can accommodate the request
    if reservation.patient_count > available:
        return ReservationResponse(
            status="CONFLICT",
            message=f"Hospital at buffer limit (Ghost Capacity protection). Requested: {reservation.patient_count}, Available: {available}",
            available=available
        )
    
    # Lock the bed(s) atomically
    collection.update_one(
        {"_id": reservation.hospital_id},
        {"$inc": {"allocated": reservation.patient_count}}
    )
    
    # Calculate new remaining capacity
    new_allocated = current_allocated + reservation.patient_count
    safe_limit = int(total_capacity * 0.85)
    remaining = safe_limit - new_allocated
    
    return ReservationResponse(
        status="SUCCESS",
        hospital=hospital["name"],
        beds_reserved=reservation.patient_count,
        remaining_capacity=remaining,
        message=f"Successfully reserved {reservation.patient_count} bed(s) at {hospital['name']}",
        available=available
    )


@app.post("/api/allocate", response_model=AllocationPlan)
async def allocate_beds(request: AllocationRequest):
    """
    Main allocation endpoint - distribute patients across nearby hospitals.
    
    Request Body:
        lat: Latitude of incident
        lon: Longitude of incident
        patient_count: Number of patients needing beds
        triage_color: Triage category (RED/YELLOW/GREEN/BLACK)
    
    Returns:
        Allocation plan with hospital assignments or overflow status
    """
    try:
        result = find_and_allocate_beds(
            lat=request.lat,
            lon=request.lon,
            patient_count=request.patient_count,
            triage_color=request.triage_color
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/reset")
async def reset_allocations():
    """
    Reset all allocated beds to 0 (for demo restarts).
    
    Returns:
        Success message with count of hospitals reset
    """
    count = reset_all_allocations()
    
    return {
        "status": "SUCCESS",
        "message": f"All allocations reset. {count} hospital(s) updated."
    }


# Phase 2 Endpoints - Radio Transcript Processing
# ============================================================================

from orchestrate_adapter import adapter as orchestration_adapter
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

@app.post("/api/radio/audio", response_model=AgentResponse)
async def process_radio_audio(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Process radio audio (WAV) through Watson STT and then Orchestrate layer.
    
    Request Body:
        audio: WAV audio file
        session_id: Optional session ID
    
    Returns:
        Agent response with action taken and session state
    """
    try:
        # 1. Transcribe Audio using Watson STT
        if not settings.watson_stt_apikey or not settings.watson_stt_url:
            raise HTTPException(status_code=500, detail="Watson STT credentials not configured")
            
        authenticator = IAMAuthenticator(settings.watson_stt_apikey)
        stt = SpeechToTextV1(authenticator=authenticator)
        stt.set_service_url(settings.watson_stt_url)
        
        # Read audio file
        audio_content = await audio.read()
        
        # Transcribe
        response = stt.recognize(
            audio=audio_content,
            content_type='audio/wav',
            model='en-US_NarrowbandModel',
            smart_formatting=True
        ).get_result()
        
        # Extract transcript
        transcript = ""
        if response.get('results'):
            transcript = response['results'][0]['alternatives'][0]['transcript']
            
        if not transcript:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
            
        # 2. Process Transcript through Agent
        # Import here to get session manager
        from sessions import session_manager
        
        # Create or use existing session
        session_id = session_id or session_manager.create_session()
        
        # Process through orchestration adapter
        result = await orchestration_adapter.process_transcript(
            transcript=transcript,
            session_id=session_id
        )
        
        return AgentResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")

@app.post("/api/radio/text", response_model=AgentResponse)
async def process_radio_text(input: RadioTranscript):
    """
    Process radio transcript through Orchestrate layer (local or cloud mode).
    
    Mode is determined by ORCHESTRATE_MODE environment variable:
    - local: Uses custom agent logic + watsonx.ai (for testing/demo)
    - production: Calls cloud watsonx Orchestrate API
    
    This endpoint bypasses speech-to-text and processes text directly.
    Useful for:
    - Testing without audio
    - Backup when microphone unavailable
    - Manual dispatcher input
    
    Request Body:
        transcript: Radio transmission text
        session_id: Optional session ID for multi-turn conversation
    
    Returns:
        Agent response with action taken and session state
    """
    try:
        # Import here to get session manager
        from sessions import session_manager
        
        # Create or use existing session
        session_id = input.session_id or session_manager.create_session()
        
        # Process through orchestration adapter (local or cloud)
        result = await orchestration_adapter.process_transcript(
            transcript=input.transcript,
            session_id=session_id
        )
        
        return AgentResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """
    Retrieve current session state.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Session state including location, casualties, transcripts
    """
    session = agent.get_session_status(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    
    return session


@app.get("/api/sessions")
async def list_sessions(status: Optional[str] = None, limit: int = 100):
    """
    List all sessions, optionally filtered by status.
    
    Query Parameters:
        status: Filter by status (ACTIVE/COMPLETED/ARCHIVED)
        limit: Maximum sessions to return (default: 100)
    
    Returns:
        List of sessions sorted by creation time (newest first)
    """
    sessions = agent.session_manager.list_sessions(status=status, limit=limit)
    
    return {
        "count": len(sessions),
        "sessions": sessions
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session (for cleanup/testing).
    
    Args:
        session_id: Session to delete
    
    Returns:
        Success message
    """
    success = agent.reset_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    
    return {
        "status": "SUCCESS",
        "message": f"Session '{session_id}' deleted"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "hospitals": "/hospitals?lat=X&lon=Y&max_km=10",
            "reserve": "POST /reserve_bed",
            "allocate": "POST /api/allocate",
            "radio_text": "POST /api/radio/text",
            "session": "GET /api/session/{id}",
            "reset": "POST /api/reset"
        }
    }
