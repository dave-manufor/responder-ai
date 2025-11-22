# **Project Master Document: Respondr.ai**

## **The Mass Casualty Triage & Logistics Assistant**

**Version:** 3.0  
**Date:** November 22, 2025  
**Status:** Hackathon Planning Phase (Production-Ready Hybrid Architecture)

---

## **1. Glossary & Definitions**

- **MCI (Mass Casualty Incident):** Any event where the number of patients exceeds immediate local resources
- **START Protocol:** "Simple Triage and Rapid Treatment" - A standard algorithm to classify patients:
  - **RED (Immediate):** Life-threatening but treatable (severe bleeding, airway compromise)
  - **YELLOW (Delayed):** Serious but stable conditions
  - **GREEN (Minor):** "Walking wounded" with non-urgent injuries
  - **BLACK (Deceased/Expectant):** Not breathing after airway positioning, or unsalvageable
- **HAvBED:** "Hospital Available Beds for Emergencies and Disasters" - Real-time bed reporting standard
- **CAD:** Computer-Aided Dispatch system used by 911 operators
- **Ghost Capacity:** The discrepancy between reported bed availability and actual capacity due to data latency
- **Safety Buffer:** Algorithmic reduction of reported capacity (using 85% of beds) to account for walk-ins and data lag
- **MongoDB GeoJSON:** Geographic data format using `[longitude, latitude]` order for 2dsphere spatial indexing
- **Stateful Session:** AI's ability to maintain context across multiple fragmented radio transmissions
- **Bulk Allocation:** Logic to distribute multiple patients (e.g., "20 burn victims") across several hospitals simultaneously

---

## **2. Solution Overview**

### **Conceptual Solution**

Respondr.ai is an **Agentic Orchestration Layer** that augments emergency dispatch systems during Mass Casualty Incidents. It autonomously:

1. **Listens** to fragmented voice reports from first responders via radio
2. **Triages** patients using the START Protocol with AI-powered entity extraction
3. **Orchestrates** hospital bed allocation using geospatial queries and real-time capacity locking
4. **Prevents** the "Patient Dumping" phenomenon where all ambulances converge on the nearest hospital

### **Core Value Proposition**

**Problem:** During disasters (e.g., Las Vegas 2017 shooting), one hospital received 200+ patients while a nearby facility received only 10. This kills people.

**Solution:** 
- **Load Balancing:** Distribute patients based on real-time capacity, not just proximity
- **Speed:** Reduce triage-to-dispatch time from ~3 minutes (manual) to ~15 seconds (autonomous)
- **Risk Mitigation:** Safety Buffer algorithm accounts for "Ghost Capacity" by using only 85% of reported beds

---

## **3. System Architecture & Data Flow**

### **The Moving Parts (Tech Stack)**

```
                    ┌──────────────────┐
                    │   Watson STT     │
                    │   (Streaming)    │
                    └────────┬─────────┘
                             │ Voice → Text
┌─────────────────┐          ▼
│   Frontend      │     ┌─────────────┐
│  (React/HTML)   │────▶│ Text Input  │ (FALLBACK)
│                 │     │ (Typed)     │
│ • Microphone    │     └──────┬──────┘
│ • Text Input    │            │ Text
└────────┬────────┘            │
         │ WebSocket           │
         └─────────────────────┼────────▶
                               ▼
┌─────────────────────────────────────────────────────────┐
│         Python Middleware (FastAPI + ADK)               │
│  • Dual Input: Voice (STT) OR Text (Direct)             │
│  • Session Manager (tracks incident state)              │
│  • Orchestration Adapter (Local/Cloud Switch)           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│    IBM watsonx Orchestrate (Multi-Agent Swarm)          │
│                                                         │
│  ┌─────────────────┐      ┌──────────────────────┐      │
│  │ Supervisor Agent│─────▶│ Session Manager Tool │      │
│  └────────┬────────┘      └──────────────────────┘      │
│           │ Delegates to:                               │
│           ▼                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Triage Agent │  │  Geo Agent   │  │  Bed Agent   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │           │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐   │
│  │ Triage Tool  │  │   Geo Tool   │  │   Bed Tool   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### **The Logic Flow (Multi-Turn Conversation)**

**Turn 1 - Location:**
```
Input: "Dispatch, Unit 1. We are at coordinates -1.29, 36.82"
Action: Create Incident_001 → Extract lat/long → Update MongoDB
Output: "Location set. Go ahead."
```

**Turn 2 - Casualty Count:**
```
Input: "We have about 20 casualties. Smoke inhalation, some unconscious"
Action: Retrieve Incident_001 → Extract count=20, injury=smoke, severity=RED
Output: Agent updates incident with casualty data
```

**Turn 3 - Orchestration:**
```
Trigger: "Requesting transport" OR 3s silence detected
Action: MongoDB $near query finds hospitals within 10km radius
Logic: Split 20 patients → 12 to Hospital A, 8 to Hospital B
Output: "Dispatching 12 to Nairobi Hospital, 8 to Aga Khan. Confirm."
```

---

## **4. Data Schemas (API Contract)**

### **A. Hospital Document (MongoDB - GeoJSON Optimized)**

```json
{
  "_id": "hosp_001",
  "name": "Nairobi Hospital",
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [36.8219, -1.2921]  // [LONG, LAT] GeoJSON ORDER!
  },
  "properties": {
    "zone": "Upper Hill",
    "icu_capacity": 12,
    "trauma_capacity": 5,
    "specialties": ["Vascular Surgery", "Neurosurgery"],
    "contact": "+254-XXX-XXXX"
  },
  "last_updated": "2025-11-22T05:27:00Z"
}
```

**MongoDB Index (CRITICAL):**
```javascript
db.hospitals.createIndex({ "geometry": "2dsphere" })
```

### **B. Incident Document (Stateful Session Tracking)**

```json
{
  "_id": "incident_2025_alpha",
  "status": "ACTIVE",
  "created_at": "2025-11-22T14:01:00Z",
  "location": { "lat": -1.2921, "long": 36.8219 },
  "casualty_log": [
    {
      "timestamp": "14:01:30",
      "transcript": "20 people with smoke inhalation",
      "extracted_count": 20,
      "triage_color": "RED",
      "primary_injury": "Smoke Inhalation"
    }
  ],
  "total_casualties": 20,
  "allocated_beds": 0
}
```

### **C. Triage Output (watsonx.ai → Orchestrate)**

```json
{
  "triage_color": "RED",
  "primary_injury": "Hemorrhagic Shock",
  "specialty_needed": "Vascular Surgery",
  "confidence_score": 0.98,
  "reasoning": "Unconscious + severe bleeding = immediate threat"
}
```

---

## **5. Intelligence Strategy: Handling Fragmentation**

### **The Stateful System Prompt (watsonx.ai)**

```
Role: You are an Emergency Dispatch AI following the START Protocol.

Context: You are updating an existing Incident Record.
Current State: {Lat: -1.29, Long: 36.82, Count: Unknown}
New Input: "We have 15 people, severe burns"

The 4 Triage Categories are:
1. Minor: Green Triage Tag Color
    Victim with relatively minor injuries
    Status unlikely to deteriorate over days
    May be able to assist in own care: also known as "walking wounded"
2. Delayed: Yellow Triage Tag Color
    Victim's transport can be delayed
    Includes serious and potentially life-threatening injuries, but status not expected to deteriorate significantly over several hours
3. Immediate: Red Triage Tag Color
    Victim can be helped by immediate intervention and transport
    Requires medical attention within minutes for survival (up to 60 minutes)
    Includes compromise to patient's airway, breathing, and circulation (the ABC's of initial resuscitation)
4. Expectant: Black Triage Tag Color
    Victim unlikely to survive given severity of injuries, level of available care, or both
    Palliative care and pain relief should be provided

Rules:
1. Extract count (convert "a dozen" → 12, "a few" → 3)
2. Classify triage using START: RED/YELLOW/GREEN/BLACK
3. Identify injury type and specialty needed
4. Use existing location if not mentioned in new input

Output (JSON ONLY):
{
  "update_type": "CASUALTY_ADDITION",
  "count": 15,
  "triage": "RED",
  "injury": "Burns",
  "specialty": "Burn Unit"
}
```

### **Training Dataset (Synthetic Generation)**

Use ChatGPT/Gemini to create 20 diverse scenarios:
- 5× RED (Critical trauma, burns, severe hemorrhage)
- 5× YELLOW (Stable fractures, moderate injuries)
- 5× GREEN (Minor cuts, panic attacks, walking wounded)
- 5× Edge Cases (No location, unclear audio, multi-casualty)

---

## **6. Development Plan & Task Allocation**

### **Strategy: "Pipes vs. Brains"**

- **Dev A (The Architect):** Infrastructure, databases, APIs, geospatial logic
- **Dev B (The Orchestrator):** AI integration, Orchestrate flows, frontend, presentation

### **Phase 1: Foundation (Hours 0-5)**

**Dev A:**
- ✅ Set up MongoDB Atlas with 2dsphere index
- ✅ Populate `hospitals.json` (mock Nairobi data)
- ✅ Build FastAPI endpoints: `GET /hospitals`, `POST /reserve_bed`
- ✅ Implement Safety Buffer logic (85% capacity rule)

**Dev B:**
- ✅ Request IBM Cloud access (watsonx.ai + Orchestrate ADK)
- ✅ Install watsonx Orchestrate ADK: `pip install ibm-watsonx-orchestrate`
- ✅ Write system prompts and test in watsonx playground
- ✅ Create frontend mockup (Figma or basic HTML)
- ✅ Generate 20 synthetic training examples
- ✅ Set up ADK project structure and skill definitions

### **Phase 2: Connectivity (Hours 5-10)**

**Dev A:**
- ✅ Implement Watson STT WebSocket in Python
- ✅ Build MongoDB geospatial query function
- ✅ Generate OpenAPI/Swagger spec

**Dev B:**
- ✅ Define Custom Skills in ADK using Dev A's API endpoints
- ✅ Create skill wrappers for MongoDB queries and bed reservation
- ✅ Connect frontend audio input to Python WebSocket
- ✅ Test STT → Middleware flow
- ✅ Implement ADK agent orchestration logic

### **Phase 3: Core Build (Hours 10-16)**

**Dev A:**
- ✅ Implement bulk allocation algorithm (split patients across hospitals)
- ✅ Build real-time dashboard WebSocket (push updates to UI)
- ✅ Add session state management (MongoDB `sessions` collection)

**Dev B:**
- ✅ **CRITICAL:** Build Multi-Agent Swarm using ADK:
  - **Tools:** Self-contained Python functions (`tools/`)
  - **Agents:** YAML definitions (`agents/`)
    - **Supervisor:** Orchestrator with `manage_session_tool`
    - **Triage Agent:** Specialist with `triage_patient_tool`
    - **Geo Agent:** Specialist with `find_hospitals_tool`
    - **Bed Agent:** Specialist with `allocate_patient_beds_tool`
  - **Orchestration:** Implement Supervisor logic to delegate tasks
- ✅ Test multi-turn conversation handling with Supervisor Agent

### **Phase 4: Integration & Testing (Hours 16-22)**

**Joint Tasks:**
- ✅ End-to-end test: Speak into mic → See bed count drop in DB
- ✅ Test bulk allocation: "20 casualties" → Split across hospitals
- ✅ Verify geospatial queries work correctly
- ✅ Test fallback to zone-based if MongoDB fails

**Dev A:**
- ✅ Polish dashboard (real-time bed counters, map visualization)
- ✅ Create database reset script for demo restarts

**Dev B:**
- ✅ Prepare demo script and presentation slides
- ✅ Record backup demo video (in case live tech fails)

### **Phase 5: Demo Polish & Contingency (Hours 22-24)**

- ✅ Final rehearsal with judges' perspective
- ✅ Test all fallback mechanisms
- ✅ Prepare elevator pitch (30 seconds)
- ✅ Set up backup laptop with pre-recorded demo

---

## **7. Implementation Details**

### **A. MongoDB Geospatial Query (Python)**

```python
from pymongo import MongoClient

def find_and_allocate_beds(lat: float, lon: float, patient_count: int):
    """
    Find nearby hospitals and allocate beds using safety buffer.
    
    Args:
        lat: Latitude of incident
        lon: Longitude of incident  
        patient_count: Number of patients needing beds
        
    Returns:
        List of hospital allocations
    """
    # Validation
    if patient_count <= 0:
        raise ValueError("Patient count must be positive")
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError("Invalid coordinates")
    
    # 1. GEOSPATIAL SEARCH: Find hospitals within 10km radius
    query = {
        "geometry": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]  # GeoJSON = [LONG, LAT]
                },
                "$maxDistance": 10000  # 10km in meters
            }
        }
    }
    
    nearby_hospitals = list(db.hospitals.find(query))  # Sorted by distance
    
    # 2. BULK ALLOCATION LOGIC with Safety Buffer
    allocation_plan = []
    remaining = patient_count
    
    for hospital in nearby_hospitals:
        if remaining <= 0:
            break
            
        # Safety Buffer: Use only 85% of reported capacity
        safe_capacity = int(hospital["properties"]["trauma_capacity"] * 0.85)
        available = safe_capacity - hospital.get("allocated", 0)
        
        if available > 0:
            allocated = min(available, remaining)
            allocation_plan.append({
                "hospital_id": hospital["_id"],
                "hospital_name": hospital["name"],
                "patients_sent": allocated,
                "coordinates": hospital["geometry"]["coordinates"],
                "distance_km": hospital.get("distance", 0) / 1000
            })
            
            # Update DB (lock beds)
            db.hospitals.update_one(
                {"_id": hospital["_id"]},
                {"$inc": {"allocated": allocated}}
            )
            remaining -= allocated
    
    if remaining > 0:
        # FALLBACK: Not enough capacity - trigger overflow protocol
        return {"status": "OVERFLOW", "unallocated": remaining, "plan": allocation_plan}
    
    return {"status": "SUCCESS", "plan": allocation_plan}
```

### **B. Dual Input API Endpoints (Voice + Text)**

```python
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
import uuid

app = FastAPI()

# WebSocket for voice (STT stream)
@app.websocket("/ws/radio")
async def radio_voice_endpoint(websocket: WebSocket):
    """Handles real-time audio → STT → Agent pipeline."""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    try:
        while True:
            # Receive transcript from Watson STT
            transcript = await websocket.receive_text()
            
            # Process with ADK agent
            result = agent.process_radio_call(transcript, session_id)
            
            # Send response back
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print(f"Voice session {session_id} disconnected")

# HTTP POST for text input (FALLBACK)
class TextInput(BaseModel):
    transcript: str
    session_id: str = None

@app.post("/api/dispatch/text")
async def dispatch_text_endpoint(input: TextInput):
    """
    Fallback for direct text input (bypasses STT).
    
    Use cases:
    - Noisy environment (STT fails)
    - Demo backup (audio issues)
    - Manual dispatcher input
    """
    session_id = input.session_id or str(uuid.uuid4())
    
    # Same agent, different input path
    result = agent.process_radio_call(input.transcript, session_id)
    
    return {
        "session_id": session_id,
        "response": result
    }

# Bed reservation endpoint
class BedReservation(BaseModel):
    hospital_id: str
    severity: str
    patient_count: int = 1

@app.post("/reserve_bed")
async def reserve_bed(reservation: BedReservation):
    """
    Reserve hospital bed(s) with safety buffer logic.
    """
    hospital = db.hospitals.find_one({"_id": reservation.hospital_id})
    
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    # REALISM ALGORITHM: Calculate safe capacity (85% of reported)
    total_beds = hospital["properties"]["trauma_capacity"]
    safe_limit = int(total_beds * 0.85)
    current_occupied = hospital.get("allocated", 0)
    
    # Check if we can accommodate the request
    if current_occupied + reservation.patient_count > safe_limit:
        return {
            "status": "CONFLICT",
            "message": "Hospital at buffer limit (Ghost Capacity protection)",
            "available": max(0, safe_limit - current_occupied)
        }
    
    # Lock the bed(s)
    db.hospitals.update_one(
        {"_id": reservation.hospital_id},
        {"$inc": {"allocated": reservation.patient_count}}
    )
    
    return {
        "status": "SUCCESS",
        "hospital": hospital["name"],
        "beds_reserved": reservation.patient_count,
        "remaining_capacity": safe_limit - (current_occupied + reservation.patient_count)
    }
```

### **C. watsonx Orchestrate ADK Implementation**

The Agent Development Kit (ADK) allows defining orchestration skills as Python functions instead of using the UI.

```python
# orchestrate_agent.py - ADK-based watsonx Orchestrate implementation
from ibm_watsonx_orchestrate import skill, agent
from typing import Dict, List
import os, requests

# SKILL 1: AI TRIAGE
@skill(name="triage_patient")
def triage_patient(transcript: str, context: Dict) -> Dict:
    """Calls watsonx.ai for START Protocol classification."""
    prompt = f"""Emergency Triage AI - START Protocol
    
Context: {context.get('location', 'Unknown location')}
Report: {transcript}

Rules: Not breathing→BLACK, >30breaths OR no pulse→RED, can't follow commands→RED, else YELLOW/GREEN
Output JSON: {{"triage_color":"RED","injury":"type","specialty":"needed"}}"""
    
    response = requests.post(
        "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation",
        headers={"Authorization": f"Bearer {os.getenv('WATSONX_TOKEN')}"},
        json={
            "model_id": "ibm/granite-13b-chat-v2",
            "input": prompt,
            "parameters": {"max_new_tokens": 150, "temperature": 0.1}
        }
    )
    return parse_json(response.json()['results'][0]['generated_text'])

# SKILL 2: GEOSPATIAL SEARCH
@skill(name="find_hospitals")
def find_hospitals(lat: float, lon: float,  max_km: int = 10) -> List[Dict]:
    """MongoDB geospatial query for nearby hospitals."""
    query = {
        "geometry": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lon, lat]},
                "$maxDistance": max_km * 1000
            }
        }
    }
    hospitals = list(db.hospitals.find(query).limit(5))
    return [{"id": str(h["_id"]), "name": h["name"], 
             "capacity": h["properties"]["trauma_capacity"]} for h in hospitals]

# SKILL 3: BED ALLOCATION
@skill(name="allocate_beds")
def allocate_beds(patient_count: int, hospitals: List[Dict]) -> Dict:
    """Distribute patients with 85% safety buffer."""
    plan = []
    remaining = patient_count
    
    for h in hospitals:
        if remaining <= 0: break
        safe_cap = int(h["capacity"] * 0.85)
        allocated = min(safe_cap - h.get("allocated", 0), remaining)
        if allocated > 0:
            db.hospitals.update_one({"_id": h["id"]}, {"$inc": {"allocated": allocated}})
            plan.append({"hospital": h["name"], "patients": allocated})
            remaining -= allocated
    
    return {"status": "SUCCESS" if remaining == 0 else "PARTIAL", 
            "plan": plan, "unallocated": remaining}

# MAIN AGENT ORCHESTRATION
@agent(name="RespondrAgent")
class RespondrAgent:
    """Coordinates all skills with session state."""
    
    def __init__(self):
        self.sessions = {}  # Multi-turn state
    
    def handle_radio(self, transcript: str, session_id: str) -> Dict:
        """Main entry: processes radio call through skill chain."""
        # Initialize or retrieve session
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "location": None, "casualties": [], "total": 0
            }
        
        session = self.sessions[session_id]
        entities = extract_entities(transcript)  # Simple regex/NLP
        
        # Update session state
        if entities.get("location"):
            session["location"] = entities["location"]
        
        # Execute skill chain
        if entities.get("casualty_count"):
            triage = triage_patient(transcript, session)
            session["casualties"].append({
                "count": entities["casualty_count"],
                "triage": triage["triage_color"]
            })
            session["total"] = sum(c["count"] for c in session["casualties"])
        
        # Trigger allocation on request
        if should_allocate(transcript, session):
            hospitals = find_hospitals(
                session["location"]["lat"], 
                session["location"]["lon"]
            )
            result = allocate_beds(session["total"], hospitals)
            return format_response(result)
        
        return {"status": "acknowledged", "session": session}

# Helper functions
def extract_entities(text): 
    """Extract location/count from text."""
    import re
    result = {}
    coords = re.search(r"(-?\d+\.?\d*),\s*(-?\d+\.?\d*)", text)
    if coords: result["location"] = {"lat": float(coords[1]), "lon": float(coords[2])}
    count = re.search(r"(\d+)\s+(?:casualties|patients)", text)
    if count: result["casualty_count"] = int(count[1])
    return result

def should_allocate(text, session):
    return ("dispatch" in text.lower() or "transport" in text.lower()) \
           and session.get("location") and session["total"] > 0

def format_response(allocation):
    parts = [f"{p['patients']} to {p['hospital']}" for p in allocation["plan"]]
    return {"message": f"Dispatching: {', '.join(parts)}. Confirm."}
```

**Why ADK over UI for Hackathons:**

| Feature | ADK (Code) | UI (Studio) |
|---------|------------|-------------|
| Speed | Edit Python, save, test | Click 10+ menus |
| Debug | Print statements, breakpoints | Console logs only |
| Version Control | Git commits | Manual export |
| Testing | Unit tests | Manual only |
| Reusability | Functions | Recreate flows |
| Best For: | **Hackathons, Production** | Quick prototypes |

---
```



### **D. Complete ADK Data Flow (Multi-Turn Conversation)**

This shows how data flows through the entire system with the ADK-based agent.

#### **Turn 1: Location Report**

```
┌─────────────────────────────────────────────────────────────┐
│  [First Responder Radio]                                    │
│  Speaks: "Unit 1 at coordinates -1.29, 36.82"               │
└────────────────────┬────────────────────────────────────────┘
                     │ Audio Stream
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [Frontend Dashboard] → [Watson STT]                        │
│  WebSocket captures audio → Real-time transcription         │
└────────────────────┬────────────────────────────────────────┘
                     │ Text: "Unit 1 at coordinates -1.29, 36.82"
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [FastAPI /ws/radio WebSocket]                              │
│  Receives: {                                                │
│    session_id: "550e8400-...",                              │
│    transcript: "Unit 1 at coordinates -1.29, 36.82"         │
│  }                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [RespondrAgent.handle_radio()]                             │
│  1. Check session: NEW → Create session state               │
│  2. Extract entities: extract_entities(transcript)          │
│     → Found: {location: {lat: -1.29, lon: 36.82}}           │
│  3. Update session:                                         │
│     session["location"] = {lat: -1.29, lon: 36.82}          │
│  4. Check should_allocate() → FALSE (no casualties yet)     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
Response: {"status": "acknowledged", "message": "Location set."}
```

**Session State After Turn 1:**
```python
{
  "location": {"lat": -1.29, "lon": 36.82},
  "casualties": [],
  "total": 0
}
```

---

#### **Turn 2: Casualty Report**

```
[Responder] "We have 20 casualties, smoke inhalation, some unconscious"
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [RespondrAgent.handle_radio()]                             │
│  1. Retrieve existing session (location already known)      │
│  2. Extract entities:                                       │
│     → {casualty_count: 20}                                  │
│  3. Trigger SKILL 1: triage_patient()                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [@skill] triage_patient(transcript, context)               │
│                                                              │
│  Prompt Built:                                              │
│  "Emergency Triage AI - START Protocol                      │
│   Context: Location -1.29, 36.82                            │
│   Report: 20 casualties, smoke inhalation, unconscious      │
│   Rules: Not breathing→BLACK, >30breaths→RED..."           │
│                                                              │
│  POST → watsonx.ai (granite-13b-chat-v2)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
watsonx.ai Response:
{
  "triage_color": "RED",
  "injury": "Smoke Inhalation",
  "specialty": "Respiratory/ICU",
  "confidence": 0.96
}
                     │
                     ▼
Update session:
session["casualties"].append({
  "count": 20,
  "triage": "RED",
  "injury": "Smoke Inhalation"
})
session["total"] = 20
```

**Session State After Turn 2:**
```python
{
  "location": {"lat": -1.29, "lon": 36.82},
  "casualties": [
    {"count": 20, "triage": "RED", "injury": "Smoke Inhalation"}
  ],
  "total": 20
}
```

---

#### **Turn 3: Transport Request (Skill Chain Activation)**

```
[Responder] "Requesting transport now"
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [RespondrAgent.handle_radio()]                             │
│  1. Extract entities: (none new)                            │
│  2. Check should_allocate():                                │
│     ✓ "transport" in text                                   │
│     ✓ location exists                                       │
│     ✓ total > 0                                             │
│     → TRUE! Trigger skill chain                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  SKILL 2: [@skill] find_hospitals(lat, lon, max_km=10)      │
│                                                              │
│  MongoDB Query:                                             │
│  {                                                           │
│    "geometry": {                                            │
│      "$near": {                                             │
│        "$geometry": {                                       │
│          "type": "Point",                                   │
│          "coordinates": [36.82, -1.29]  // [LON, LAT]!      │
│        },                                                    │
│        "$maxDistance": 10000  // 10km in meters             │
│      }                                                       │
│    }                                                         │
│  }                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
MongoDB Results (sorted by distance):
[
  {
    id: "hosp_001",
    name: "Kenyatta National Hospital",
    capacity: 20,
    allocated: 0,
    distance: 2.3km
  },
  {
    id: "hosp_002", 
    name: "Nairobi Hospital",
    capacity: 8,
    allocated: 0,
    distance: 4.1km
  },
  {
    id: "hosp_003",
    name: "Aga Khan Hospital",
    capacity: 12,
    allocated: 0,
    distance: 6.7km
  }
]
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  SKILL 3: [@skill] allocate_beds(patient_count=20, hospitals)│
│                                                              │
│  Algorithm (85% Safety Buffer):                             │
│  ───────────────────────────────────────────────────────    │
│  Hospital 1: Kenyatta                                       │
│    Total Capacity: 20                                       │
│    Safe Capacity: 20 * 0.85 = 17 beds                       │
│    Allocated: 0                                             │
│    Available: 17                                            │
│    → Allocate: min(17, 20) = 17 patients                    │
│    → Remaining: 20 - 17 = 3                                 │
│                                                              │
│  Hospital 2: Nairobi                                        │
│    Total Capacity: 8                                        │
│    Safe Capacity: 8 * 0.85 = 6 beds                         │
│    Allocated: 0                                             │
│    Available: 6                                             │
│    → Allocate: min(6, 3) = 3 patients                       │
│    → Remaining: 3 - 3 = 0 ✓                                 │
│                                                              │
│  MongoDB Updates:                                           │
│  db.hospitals.update_one(                                   │
│    {"_id": "hosp_001"},                                     │
│    {"$inc": {"allocated": 17}}                              │
│  )                                                           │
│  db.hospitals.update_one(                                   │
│    {"_id": "hosp_002"},                                     │
│    {"$inc": {"allocated": 3}}                               │
│  )                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
Allocation Result:
{
  "status": "SUCCESS",
  "plan": [
    {"hospital": "Kenyatta National Hospital", "patients": 17},
    {"hospital": "Nairobi Hospital", "patients": 3}
  ],
  "unallocated": 0
}
                     │
                     ▼
format_response() →
{
  "message": "Dispatching: 17 to Kenyatta National Hospital, 3 to Nairobi Hospital. Confirm."
}
```

---

#### **Turn 4: Dashboard Visualization**

```
┌─────────────────────────────────────────────────────────────┐
│  [WebSocket → Frontend]                                     │
│  Sends allocation result to React dashboard                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  [React Dashboard Updates]                                  │
│                                                              │
│  1. Hospital Bed Counters:                                  │
│     ┌─────────────────────────────────────┐                │
│     │ Kenyatta: 20 → 3 remaining (17🚑)   │                │
│     │ Nairobi:   8 → 5 remaining (3🚑)    │                │
│     │ Aga Khan: 12 → 12 remaining         │                │
│     └─────────────────────────────────────┘                │
│                                                              │
│  2. Map Visualization (Leaflet/Mapbox):                     │
│     ┌─────────────────────────────────────┐                │
│     │  🔴 Incident (-1.29, 36.82)          │                │
│     │   │                                  │                │
│     │   ├──────17──────▶ 🏥 Kenyatta 2.3km │                │
│     │   │                                  │                │
│     │   └──────3───────▶ 🏥 Nairobi 4.1km  │                │
│     │                                      │                │
│     │      (dashed)     🏥 Aga Khan 6.7km  │                │
│     │                                      │                │
│     │  ⭕ 10km radius circle               │                │
│     └─────────────────────────────────────┘                │
│                                                              │
│  3. Confirmation Message:                                   │
│     "Dispatching: 17 to Kenyatta National Hospital,         │
│      3 to Nairobi Hospital. Confirm."                       │
└─────────────────────────────────────────────────────────────┘
```

---

### **Key Data Structures**

#### **1. Session State (Maintained by RespondrAgent)**
```python
self.sessions[session_id] = {
  "location": {"lat": float, "lon": float},
  "casualties": [
    {"count": int, "triage": str, "injury": str}
  ],
  "total": int,
  "allocated": [
    {"hospital": str, "patients": int}
  ]
}
```

#### **2. Skill Outputs**

**Triage Skill:**
```python
{
  "triage_color": "RED" | "YELLOW" | "GREEN" | "BLACK",
  "injury": str,
  "specialty": str,
  "confidence": float
}
```

**Find Hospitals Skill:**
```python
[
  {
    "id": str,
    "name": str,
    "capacity": int,
    "allocated": int,
    "distance": float  # in km
  }
]
```

**Allocate Beds Skill:**
```python
{
  "status": "SUCCESS" | "PARTIAL" | "FAILED",
  "plan": [
    {"hospital": str, "patients": int}
  ],
  "unallocated": int
}
```

---

### **ADK vs UI: Data Flow Differences**

| Aspect | **ADK (Current)** | **UI-Based (Old)** |
|--------|-------------------|-------------------|
| **Orchestration** | Python function calls in RespondrAgent.handle_radio() | Visual flow designer in browser |
| **Session State** | `self.sessions` dictionary in Python | External state management required |
| **Debugging** | Print statements, breakpoints, logs | Browser console only |
| **Skill Execution** | Direct function calls: `triage_patient(...)` | HTTP callbacks to skill endpoints |
| **Error Handling** | Try/except blocks in Python | UI-configured retry logic |
| **Testing** | Unit tests for each skill | Manual testing in UI |
| **Version Control** | Git commits of Python code | Export/import JSON configs |

**Key Advantage:** With ADK, the entire orchestration logic is **transparent Python code** that can be read, tested, and debugged like any other application code.

---

### **E. Mocking CAD System Integration (Unit GPS/AVL)**

In real dispatch systems, responder locations come from the CAD (Computer-Aided Dispatch) system via GPS/AVL, not verbal coordinates. Responders say **"Unit 1 here"** not lat/long.

#### **Mock CAD Data (cad_mock.py)**

```python
# cad_mock.py - Simulates CAD/AVL system
from typing import Dict, Optional
from datetime import datetime

class CADSystem:
    """Mock CAD with GPS tracking (simulates Motorola/Hexagon/Tyler CAD)."""
    
    def __init__(self):
        self.units = {
            "Unit 1": {
                "type": "Ambulance",
                "status": "En Route",
                "location": {"lat": -1.2921, "lon": 36.8219},
                "last_update": "2025-11-22T14:01:00Z"
            },
            "Medic 1": {
                "type": "Paramedic Unit", 
                "status": "Available",
                "location": {"lat": -1.2950, "lon": 36.8150},
                "last_update": "2025-11-22T14:00:00Z"
            },
            "Engine 5": {
                "type": "Fire Engine",
                "status": "On Scene",
                "location": {"lat": -1.2880, "lon": 36.8280},
                "last_update": "2025-11-22T14:03:00Z"
            }
        }
    
    def get_unit_location(self, unit_id: str) -> Optional[Dict]:
        """Get GPS location from CAD (simulates AVL feed)."""
        unit = self.units.get(unit_id)
        return unit["location"] if unit else None

cad_system = CADSystem()
```

#### **Enhanced Entity Extraction with CAD Lookup**

```python
def extract_entities(text): 
    """Extract unit ID and lookup GPS from CAD."""
    import re
    result = {}
    
    # Match unit patterns: "Unit 1", "Medic 1", "Engine 5"
    unit_match = re.search(r"(Unit|Medic|Engine|Ambulance)\s+(\d+)", text, re.IGNORECASE)
    if unit_match:
        unit_id = f"{unit_match.group(1).title()} {unit_match.group(2)}"
        
        # LOOKUP IN CAD (this is the magic!)
        location = cad_system.get_unit_location(unit_id)
        if location:
            result["unit_id"] = unit_id
            result["location"] = location
            result["location_source"] = "CAD_GPS"  # Not verbal!
    
    # Fallback: manual coordinates (emergency override)
    if "location" not in result:
        coords = re.search(r"(-?\d+\.?\d*),\s*(-?\d+\.?\d*)", text)
        if coords:
            result["location"] = {"lat": float(coords[1]), "lon": float(coords[2])}
            result["location_source"] = "MANUAL"
    
    # Extract casualty count
    count = re.search(r"(\d+)\s+(?:casualties|patients)", text)
    if count:
        result["casualty_count"] = int(count[1])
    
    return result
```

#### **CAD API Endpoints**

```python
# main.py
from cad_mock import cad_system

@app.get("/api/cad/units")
async def list_units():
    """List all active units (for map display)."""
    return {"units": cad_system.units}

@app.get("/api/cad/unit/{unit_id}")
async def get_unit(unit_id: str):
    """Get unit's GPS location."""
    loc = cad_system.get_unit_location(unit_id)
    if not loc:
        raise HTTPException(404, "Unit not in CAD")
    return {"unit_id": unit_id, "location": loc}
```

#### **Realistic Demo Flow**

**Turn 1: Unit Identification**
```
Input: "Dispatch, this is Unit 1"
       ↓
extract_entities() finds "Unit 1"
       ↓
cad_system.get_unit_location("Unit 1")
       ↓
Returns: {"lat": -1.2921, "lon": 36.8219}
       ↓
Session location AUTO-POPULATED from CAD!
```

**Turn 2: Casualty Report**
```
Input: "We have 20 casualties, smoke inhalation"
       (Location already set from CAD GPS)
```

#### **Frontend CAD Display**

```javascript
// Show active units on map
fetch('/api/cad/units')
  .then(res => res.json())
  .then(data => {
    Object.entries(data.units).forEach(([id, unit]) => {
      addUnitMarker(unit.location.lat, unit.location.lon, id, unit.status);
    });
  });
```

#### **Demo Script (Realistic)**

```
✅ "Dispatch, Unit 1 here, we have a mass casualty"
✅ "Medic 1 on scene, approximately 20 patients"
✅ "Engine 5, requesting ambulance transport"

❌ "We are at -1.29, 36.82" (unrealistic!)
```

#### **Benefits**

| Without CAD | With CAD Mock |
|-------------|---------------|
| Responders say coords | Responders say unit ID |
| Awkward demo | Natural radio talk |
| "Seems fake" | "This is how CAD works!" |
| Hard to explain | Points to real systems |

---







## **8. Hackathon Survival Checklist**

### **Critical Rules**

1. **Demo > Code:** If the geospatial math breaks, fallback to zone matching. Judges score what they SEE working.

2. **Dual Input Mode (CRITICAL for Demo):**
   - **Voice Input:** Watson STT via `/ws/radio` WebSocket
   - **Text Input (FALLBACK):** Direct text via `/api/dispatch/text` POST
   - Frontend should have BOTH:
     - 🎤 Microphone button for live voice
     - ⌨️ Text input box for typing
   - If STT fails during demo, seamlessly switch to typing
   - Pre-record 3 demo audio files as backup
   - Example text inputs for demo:
     ```
     "Unit 1 at coordinates -1.29, 36.82"
     "We have 20 casualties, smoke inhalation, some unconscious"
     "Requesting transport now"
     ```

3. **Reset Button:**
   ```python
   @app.post("/admin/reset_demo")
   async def reset_demo():
       """Reset all hospital bed counts to initial state"""
       db.hospitals.update_many({}, {"$set": {"allocated": 0}})
       db.incidents.delete_many({"status": "DEMO"})
       return {"status": "Demo reset successful"}
   ```

4. **GeoJSON Coordinate Order:** 
   - ALWAYS `[longitude, latitude]` for MongoDB
   - If you swap them, you'll be searching Antarctica
   - Add assertion: `assert -180 <= lon <= 180`

5. **The "Silence Hack":**
   - If real-time silence detection is hard, use voice command: "Over" or "Dispatch"
   - Middleware triggers on keyword instead of 3s pause

6. **Fallback Layers:**
   - **Level 1:** MongoDB geospatial (the goal)
   - **Level 2:** Zone-based matching (if geo breaks)
   - **Level 3:** Hardcoded hospital (if all DB fails)
   - **Level 4:** Pre-recorded video (if everything burns)

7. **Visual Wins:**
   - Map with lines from incident → hospitals
   - Real-time bed counter animation
   - Color-coded triage badges (RED/YELLOW/GREEN)

---

## **9. Presentation Strategy**

### **The Judging Criteria**

1. **Application of Technology (30%):** Multi-model AI pipeline (STT + LLM + Orchestrate)
2. **Business Value (30%):** Prevents deaths from patient dumping
3. **Originality (25%):** Bulk allocation + stateful sessions
4. **Presentation (15%):** Live demo quality

### **The 3-Minute Demo Flow**

```
MINUTE 1: The Problem
├─ Show: Chaotic ER photo
├─ Stat: "2017 Vegas shooting: 1 hospital got 200 patients, another got 10"
└─ Thesis: "Patient dumping kills people. AI can fix this."

MINUTE 2: The Demo (LIVE)
├─ Play audio: "Severe burns, 20 casualties at stadium"
├─ Show: Dashboard updates in real-time
│   ├─ Triage badge turns RED
│   ├─ Map draws radius from incident
│   └─ Bed counters drop: Hospital A (-12), Hospital B (-8)
└─ Confirmation: "Zero overcrowding. Zero phone calls."

MINUTE 3: The Tech
├─ Show: Architecture diagram (60 seconds)
├─ Highlight: "Multi-turn AI remembers context"
└─ Close: "This tech exists today. We just integrated it."
```

### **Slide Structure (5 Slides Max)**

1. **Problem:** Patient dumping statistics + photo
2. **Solution:** One-sentence value prop + architecture diagram
3. **Demo:** Live screen recording (backup if tech fails)
4. **Originality:** Bulk allocation + safety buffer algorithm
5. **Call to Action:** "Deploy in Nairobi County within 6 months"

### **Keywords for Submission**

- **Primary Technology:** IBM watsonx Orchestrate
- **Secondary Technologies:** watsonx.ai, Watson STT, MongoDB
- **Category:** Healthcare / Emergency Response / AI Agents
- **Tags:** #AgenticAI #DisasterResponse #GovTech #RealtimeAI #Geospatial

---

## **10. FALLBACK PLAN (Critical for Demos)**

### **Technology Failure Matrix**

| Component | Failure Mode | Fallback Action | Prep Required |
|-----------|-------------|-----------------|---------------|
| **MongoDB** | Connection timeout | Use zone-based fallback | Have zone lookup table |
| **Watson STT** | WebSocket drops | Use pre-recorded transcripts | Have 3 text files ready |
| **watsonx.ai** | API rate limit | Use hardcoded triage rules | IF/THEN logic in Python |
| **Orchestrate** | Skill chain breaks | Direct Python API calls | Standalone functions |
| **Internet** | Complete outage | Play backup video | 2-min screen recording |

### **The Nuclear Option: Offline Mode**

If everything fails, have a **fully functional local version**:

```python
# Simplified offline triage (no AI needed)
def offline_triage(transcript: str) -> str:
    keywords_red = ["unconscious", "severe", "bleeding", "burns"]
    keywords_yellow = ["fracture", "stable", "moderate"]
    
    transcript_lower = transcript.lower()
    
    if any(word in transcript_lower for word in keywords_red):
        return "RED"
    elif any(word in transcript_lower for word in keywords_yellow):
        return "YELLOW"
    else:
        return "GREEN"
```

### **Demo Day Checklist (Print This)**

- [ ] Laptop fully charged + power adapter
- [ ] Backup laptop with identical setup
- [ ] 3 pre-recorded audio files loaded
- [ ] 1 backup demo video (2 minutes)
- [ ] Database reset script tested
- [ ] All API keys in `.env` file (backup copy in Google Drive)
- [ ] Presentation slides exported as PDF (in case PowerPoint crashes)
- [ ] Team roles decided: Who speaks, who controls laptop
- [ ] 30-second elevator pitch memorized

---

## **11. Success Metrics**

### **Technical Milestones**

- [ ] Watson STT successfully streams audio → text
- [ ] watsonx.ai correctly triages 18/20 test cases
- [ ] MongoDB geospatial returns hospitals within 10km
- [ ] Bulk allocation splits 20 patients across 2+ hospitals
- [ ] Safety buffer prevents overcrowding (85% rule enforced)
- [ ] Multi-turn session maintains state across 3 turns
- [ ] Dashboard updates in <2 seconds after speech ends

### **Demo Milestones**

- [ ] Live demo runs without crashes (1 attempt)
- [ ] Backup demo video plays smoothly
- [ ] Judges understand the problem statement
- [ ] At least 2 judges ask technical questions
- [ ] Team stays under 5-minute presentation limit

### **Hackathon Win Conditions**

**Bronze:** Working STT → Triage → Single hospital allocation  
**Silver:** + Multi-turn sessions + Geospatial queries  
**Gold:** + Bulk allocation + Live demo success + Strong presentation

---

## **Appendix A: Sample Data**

### **hospitals.json (Nairobi Mock Data)**

```json
[
  {
    "_id": "hosp_001",
    "name": "Kenyatta National Hospital",
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [36.8078, -1.3006]},
    "properties": {
      "zone": "Upper Hill",
      "icu_capacity": 45,
      "trauma_capacity": 20,
      "specialties": ["Trauma", "Burns", "Neurosurgery"]
    }
  },
  {
    "_id": "hosp_002",
    "name": "Nairobi Hospital",
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [36.8219, -1.2921]},
    "properties": {
      "zone": "Upper Hill",
      "icu_capacity": 12,
      "trauma_capacity": 8,
      "specialties": ["Vascular", "Cardiothoracic"]
    }
  },
  {
    "_id": "hosp_003",
    "name": "Aga Khan University Hospital",
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [36.8169, -1.2673]},
    "properties": {
      "zone": "Parklands",
      "icu_capacity": 18,
      "trauma_capacity": 12,
      "specialties": ["Trauma", "Orthopedics", "Neurosurgery"]
    }
  }
]
```

---

## **Appendix B: Critical Reminders**

### **For Dev A:**
- GeoJSON is `[longitude, latitude]` NOT `[lat, long]`
- Always use Safety Buffer (85%) in bed calculations
- Test with coordinates: Nairobi = `[-1.2921, 36.8219]`

### **For Dev B:**
- watsonx prompts must return ONLY valid JSON
- Test with edge cases: "uh... about... maybe 12 people?"
- Orchestrate skills can timeout - keep prompts under 30 tokens

### **For Both:**
- Commit code every 2 hours
- Test the reset button every hour
- Have fun - this is a hackathon, not production!

---

**END OF DOCUMENT**

*Version 3.0 merges the pragmatic hackathon survival of V1 with the technical sophistication of V2. Build what works, demo what impresses, fallback when needed.*