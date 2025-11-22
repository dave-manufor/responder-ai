# API Integration Guide - Respondr.ai

## Overview
This guide details how to connect the frontend application to the Respondr.ai backend. The backend provides RESTful endpoints for incident management, hospital data, and AI-driven triage.

## Base URL
- **Local Development**: `http://localhost:8000`
- **Production**: `https://api.respondr.ai` (Example)

## Authentication
Currently, the API is open and does not require authentication tokens for the hackathon demo version.

## Core Workflows

### 1. Initialization
When the application starts:
1. **Check Health**: Call `GET /health` to ensure the backend is reachable.
2. **Load Hospitals**: Call `GET /hospitals` to populate the map.
3. **Check/Create Session**:
   - Check local storage for a `session_id`.
   - If exists, call `GET /api/session/{session_id}` to restore state.
   - If not, the first interaction with `POST /api/radio/text` will create one.

### 2. Incident Reporting (Dual Input)
The primary way to interact with the system is through natural language (voice or text).

#### Text Input
1. User types a message (e.g., "We have 5 casualties at the stadium").
2. Frontend sends `POST /api/radio/text`:
   ```json
   {
     "transcript": "We have 5 casualties at the stadium",
     "session_id": "optional-uuid-here"
   }
   ```
3. Backend processes text, updates session, and returns `AgentResponse`.

#### Voice Input
1. Frontend records audio using browser MediaRecorder API (must be WAV format).
2. Frontend sends the audio file to `POST /api/radio/audio` as `multipart/form-data`.
   ```javascript
   const formData = new FormData();
   formData.append('audio', audioBlob, 'recording.wav');
   formData.append('session_id', currentSessionId);
   
   await fetch('/api/radio/audio', { method: 'POST', body: formData });
   ```
3. Backend transcribes and processes it, returning `AgentResponse`.

### 3. Handling Agent Responses
The `AgentResponse` object dictates the frontend state updates:

```json
{
  "session_id": "uuid...",
  "transcript": "Original text...",
  "action": "casualty_reported",
  "message": "Acknowledged. Triage: RED...",
  "session_state": { ... },
  "triage_result": { ... },
  "allocation_result": { ... }
}
```

- **`action`**:
  - `acknowledged`: Simple confirmation.
  - `location_updated`: Update map marker.
  - `casualty_reported`: Update triage counts.
  - `beds_allocated`: Draw allocation lines on map.
  - `error`: Show error toast.

### 4. Real-time Updates
Since WebSockets are not currently implemented, the frontend should poll for updates if multiple users are simulating the same incident.
- **Polling Interval**: 2-5 seconds.
- **Endpoint**: `GET /api/session/{session_id}`.

## Error Handling
- **404 Not Found**: Usually means an invalid session ID. Clear local storage and start fresh.
- **500 Internal Server Error**: Display a generic "System Error" message and check console logs.

## Mocking & Testing
- Use `POST /api/reset` to clear all allocations and start a fresh demo scenario.
