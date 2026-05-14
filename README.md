# Responder AI

AI-powered emergency response assistant that provides intelligent triage, geospatial hospital routing, and real-time incident coordination. Built with Google's Agent Development Kit (ADK).

## Architecture

```
responder-ai/
├── backend/
│   ├── agents/               # AI agent definitions
│   ├── tools/                # Custom agent tools
│   ├── agent.py              # Main agent orchestration
│   ├── triage_service.py     # Emergency triage logic
│   ├── geospatial.py         # Location-based hospital routing
│   ├── database.py           # Data persistence layer
│   ├── sessions.py           # Session management
│   ├── models.py             # Data models
│   ├── config.py             # Application configuration
│   └── hospitals.json        # Hospital geospatial data
├── frontend/                 # Web interface (HTML/CSS/JS)
└── docs/
    └── project-overview.md   # Project documentation
```

## Tech Stack

| Layer           | Technology                                |
|-----------------|-------------------------------------------|
| **AI Framework**| Google ADK (Agent Development Kit)        |
| **Backend**     | Python, FastAPI                           |
| **Frontend**    | HTML, CSS, JavaScript                     |
| **AI/ML**       | LLM-powered agents, orchestration         |
| **Geospatial**  | Location-based hospital routing           |
| **Data**        | JSON-based hospital registry, SQLite      |

## Key Features

- **Intelligent Triage** — AI agents assess emergency severity and recommend appropriate response levels
- **Geospatial Routing** — Finds nearest hospitals based on location data and available capacity
- **Agent Orchestration** — Multi-agent system with hybrid orchestration for complex emergency scenarios
- **Session Management** — Persistent conversation state for ongoing incident tracking
- **Deployment Tools** — Built-in deployment utilities for rapid provisioning

## Research & Documentation

The project includes detailed research notes on:
- `ADK_RESEARCH.md` — Google ADK integration patterns
- `ORCHESTRATE_HYBRID.md` — Hybrid agent orchestration strategies
- `PHASE2_TEST_RESULTS.md` — Testing and validation results
- `SESSION_MIGRATION.md` — Session state management
- `SETUP.md` — Environment setup guide

## Getting Started

```bash
# Clone the repository
git clone https://github.com/dave-manufor/responder-ai.git
cd responder-ai

# Backend setup
cd backend
pip install -r requirements.txt
python main.py

# Frontend (separate terminal)
cd frontend
# Open index.html or serve with a local server
```

## License

MIT
