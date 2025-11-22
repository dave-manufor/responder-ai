# Frontend Dashboard Requirements - Respondr.ai

## **Overview**
This document outlines the comprehensive requirements for the Respondr.ai frontend dashboard used for mass casualty incident management during hackathon demonstrations and potential production deployment.

---

## **1. Dual Input Interface**

### **Voice Input**
- 🎤 Microphone button to capture audio.
- **Implementation**:
    - Record audio in browser (WAV format).
    - Send audio file to `POST /api/radio/audio`.
    - Backend handles transcription via Watson STT.
- **Visuals**:
    - Visual indicator when recording.
    - Real-time transcription display (optional, if using client-side STT for preview, otherwise show "Processing...").

### **Text Input (Fallback)**
- ⌨️ Text input box for typing dispatches.
- **Endpoint**: `POST /api/radio/text`
- **Features**:
    - Submit button + Enter key support.
    - Session ID tracking (optional, backend handles new sessions).
    - Example prompts dropdown for quick demo.

---

## **2. Interactive Map (Leaflet or Mapbox)**

### **Must Display:**
- 🔴 **Incident location** (red marker) - from manual input or session state.
- 🏥 **Hospital markers** (blue) - fetched from `/hospitals`.
- ⭕ **10km search radius** circle around incident (visual only, backend handles logic).
- ➡️ **Allocation lines** from incident to hospitals (visualize `AllocationPlan`).

### **Map Interactions:**
- Click hospital marker → Show details (Name, Zone, ICU/Trauma Capacity).
- Pan/zoom controls.

### **Real-time Updates:**
- Poll `/api/session/{session_id}` to get latest state (allocations, casualty counts).
- Update hospital markers based on `allocated` count from `/hospitals`.

---

## **3. Hospital Capacity Dashboard**

### **For Each Hospital:**
```
┌──────────────────────────────┐
│ Kenyatta National Hospital   │
│ ────────────────────────────│
│ Trauma Capacity: 20          │
│ Allocated: 5                 │
│ [█████░░░░░░░░░░░░░░░]       │
│ Zone: Central                │
│ Specialties: Trauma, Burn    │
│ Distance: 2.3 km             │
└──────────────────────────────┘
```

### **Features:**
- Fetch from `/hospitals`.
- Show `trauma_capacity` and `allocated`.
- Calculate available beds locally or use backend logic.
- Display "Ghost Capacity" warning if near limit (backend handles buffer logic).

---

## **4. Triage Display Panel**

### **Current Incident Summary:**
```
┌──────────────────────────────┐
│ SESSION: {session_id}        │
│ Status: ACTIVE               │
│ ────────────────────────────│
│ Casualties by Triage:        │
│ 🔴 RED (Immediate): 15        │
│ 🟡 YELLOW (Delayed): 3        │
│ 🟢 GREEN (Minor): 2           │
│ ⚫ BLACK (Expectant): 0      │
│ ────────────────────────────│
│ Total: 20 casualties          │
│ Allocated: 20/20 ✅          │
└──────────────────────────────┘
```

### **Features:**
- Fetch from `/api/session/{session_id}`.
- Display `casualty_log` entries.
- Show `total_casualties` and `allocated_beds`.

---

## **5. Transcript & Response Log**

### **Conversation History:**
```
[User] "We have 20 casualties, smoke inhalation"
[AI]   "Acknowledged. Triage: RED. Total casualties: 20. Request transport when ready."
       Action: casualty_reported
```

### **Features:**
- Display `transcript` and `message` from `AgentResponse`.
- List history from `/api/session/{session_id}` (`casualty_log` or similar if stored).
- **Note**: The current backend `Incident` model stores `casualty_log` but full conversation history might need client-side tracking or session polling.

---

## **6. Allocation Results Panel**

### **When Transport Requested:**
```
┌──────────────────────────────────────┐
│ ALLOCATION PLAN                      │
│ ────────────────────────────────────│
│ ✅ 17 patients → Kenyatta Hospital   │
│    Distance: 2.3 km                  │
│                                      │
│ ✅ 3 patients → Nairobi Hospital     │
│    Distance: 4.1 km                  │
│ ────────────────────────────────────│
│ Status: SUCCESS ✅                   │
│ Message: Successfully allocated...   │
└──────────────────────────────────────┘
```

### **Features:**
- Display result from `POST /api/allocate` or `AgentResponse` (if action is `beds_allocated`).
- Show `plan` details: hospital name, patient count, distance.
- Show `status` (SUCCESS, PARTIAL, OVERFLOW).

---

## **7. Demo Control Panel**

### **For Hackathon Presentation:**
- 🔄 **Reset Demo** button → `POST /api/reset`.
- 📊 **Session Info** → Display current Session ID.

---

## **8. Technical Requirements**

### **API Integration:**
- **Base URL**: `http://localhost:8000`
- **Endpoints**:
    - `GET /health`: Check backend status.
    - `GET /hospitals`: Get hospital list (supports lat/lon/max_km).
    - `POST /reserve_bed`: Reserve specific beds (manual override).
    - `POST /api/allocate`: Bulk allocation.
    - `POST /api/radio/text`: Main interaction endpoint (text/voice transcript).
    - `GET /api/session/{id}`: Get session state.
    - `POST /api/reset`: Reset allocations.

### **State Management:**
- Store `session_id` in local storage or context.
- Poll `/api/session/{session_id}` every few seconds for updates (if multi-user/async) or update on API response.

---

## **9. UI/UX Priorities**

### **Color Scheme:**
- **Triage**:
    - 🔴 RED (#DC2626)
    - 🟡 YELLOW (#FBBF24)
    - 🟢 GREEN (#10B981)
    - ⚫ BLACK (#1F2937)
- **Map**:
    - Incident: Red
    - Hospitals: Blue
    - Allocations: Purple

---

## **10. Error Handling**

### **Visual Feedback:**
- Toast notifications for API success/failure.
- Handle `404 Session Not Found` (prompt to create new).
- Handle `500 Agent Error` (show raw error for debugging).

---

## **11. Development Priority (Hackathon)**

### **Phase 1: Core Connectivity**
- [ ] Connect to `GET /health` and `GET /hospitals`.
- [ ] Implement Map with Hospital markers.

### **Phase 2: Interaction**
- [ ] Implement `POST /api/radio/text` input.
- [ ] Display `AgentResponse` (message, action).

### **Phase 3: State & Visualization**
- [ ] Visualize `AllocationPlan` on map.
- [ ] Show Triage Summary from Session state.

### **Phase 4: Polish**
- [ ] Voice input (browser STT).
- [ ] Auto-refresh/polling.

---

**Document Version:** 2.0 (Aligned with Backend)
**Last Updated:** 2025-11-22
