# Respondr.ai 🚑

**The Mass Casualty Triage & Logistics Assistant**

Respondr.ai is an **Agentic Orchestration Layer** that augments emergency dispatch systems during Mass Casualty Incidents (MCIs). It autonomously listens to fragmented voice reports from first responders via radio, triages patients using the START Protocol, and orchestrates hospital bed allocation using real-time geospatial queries and capacity locking to prevent "Patient Dumping" (where all ambulances converge on the nearest hospital).

---

## 🌟 Core Value Proposition

- **Load Balancing:** Distributes patients based on real-time capacity rather than just proximity.
- **Speed:** Reduces triage-to-dispatch time from ~3 minutes (manual) to ~15 seconds (autonomous).
- **Risk Mitigation:** Uses a "Safety Buffer" algorithm to account for "Ghost Capacity," utilizing only 85% of reported beds to leave room for walk-ins.

---

## 🏗 System Architecture

The project leverages a Multi-Agent Swarm powered by **IBM watsonx Orchestrate**.

```text
Voice (Watson STT) / Text Input
          │
          ▼
Python Middleware (FastAPI + WebSocket)
          │
          ▼
IBM watsonx Orchestrate (Multi-Agent Swarm)
 ├── Supervisor Agent
 │    └── Session Manager Tool
 ├── Triage Agent
 │    └── Triage Tool
 ├── Geo Agent
 │    └── Geo Tool
 └── Bed Agent
      └── Bed Tool
```

### Components
- **Frontend:** React + Vite (WebSockets for real-time audio)
- **Middleware:** FastAPI (Python), WebSocket streaming
- **AI/Triage:** IBM watsonx.ai (`ibm/granite-13b-chat-v2`)
- **Orchestration:** IBM watsonx Orchestrate ADK (`ibm-watsonx-orchestrate`)
- **Database:** MongoDB Atlas (GeoJSON optimized with 2dsphere indexing)

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python 3.9+
- MongoDB (running locally or Atlas URI)
- IBM watsonx credentials

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Create .env file
# MONGO_URI=mongodb://localhost:27017
# WATSONX_TOKEN=your_token_here

# Start the server
uvicorn main:app --reload
# Runs at http://localhost:8000
# API Docs at http://localhost:8000/docs
```

### 2. Frontend Configuration
The frontend is built with React + Vite.

```bash
cd frontend
npm install

# Create a .env file
# VITE_API_BASE_URL=http://localhost:8000

# Start development server
npm run dev
```

---

## 🧠 Intelligence Strategy: Multi-Turn Sessions

Respondr.ai maintains a stateful session to track incident status across multiple fragmented radio transmissions:

1. **Turn 1 (Location):** "Unit 1 at coordinates -1.29, 36.82" -> Creates incident record in MongoDB.
2. **Turn 2 (Casualty Count):** "20 casualties, smoke inhalation" -> Extracted by LLM and triaged via START Protocol (e.g., RED).
3. **Turn 3 (Orchestration):** "Requesting transport" -> Triggers geospatial search and bulk bed allocation with 85% safety buffer.

---

## 📄 License
MIT License
