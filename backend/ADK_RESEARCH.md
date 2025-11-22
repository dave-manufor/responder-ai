# watsonx Orchestrate ADK: Deep Dive & Best Practices

## Overview
The watsonx Orchestrate Agent Development Kit (ADK) allows developers to build, test, and deploy AI agents and custom tools. This document outlines the structure, definition, and deployment processes based on official documentation.

## 1. Developing Tools

### Definition
Tools are Python functions decorated with `@tool` from `ibm_watsonx_orchestrate.agent_builder.tools`. They must have Google-style docstrings which the LLM uses to understand how and when to use the tool.

### Structure
*   **File**: `my_tools.py` (can contain multiple tools)
*   **Dependencies**: `requirements.txt` (must be in the same directory or specified during import)
*   **Best Practice**: Keep tools stateless. If state is needed, pass it via arguments or manage it externally (e.g., database).

### Example
```python
from ibm_watsonx_orchestrate.agent_builder.tools import tool

@tool
def get_weather(city: str) -> dict:
    """
    Get weather for a city.
    
    Args:
        city (str): Name of the city.
        
    Returns:
        dict: Weather info.
    """
    return {"temp": 25, "city": city}
```

## 2. Developing Agents

### Definition
Agents are defined using YAML or JSON configuration files. They specify the model, system prompt (instructions), tools, and collaborators.

### Structure
*   **File**: `agent_config.yaml`
*   **Key Fields**:
    *   `name`: Unique name.
    *   `description`: What the agent does.
    *   `model`: LLM ID (e.g., `ibm/granite-3-8b-instruct`).
    *   `tools`: List of tool names (must be imported first).
    *   `collaborators`: List of other agent names (for multi-agent swarms).
    *   `instructions`: System prompt guiding behavior and delegation.

### Example
```yaml
name: "Supervisor Agent"
description: "Coordinates the swarm"
model: "ibm/granite-3-8b-instruct"
collaborators:
  - "Triage Agent"
  - "Geo Agent"
instructions: |
  You are a supervisor. Delegate tasks to your collaborators.
  - For medical issues, ask Triage Agent.
  - For location issues, ask Geo Agent.
```

## 3. Directory Structure (Recommended)

```
project_root/
├── agents/
│   ├── supervisor.yaml
│   ├── triage_agent.yaml
│   └── geo_agent.yaml
├── tools/
│   ├── __init__.py
│   ├── medical_tools.py
│   ├── geo_tools.py
│   └── requirements.txt  <-- Specific to tools
├── .env
└── main.py
```

## 4. Deployment Workflow (CLI)

The standard deployment process uses the `orchestrate` CLI.

### Step 1: Import Tools
Uploads the Python code and installs dependencies in the Orchestrate environment.
```bash
orchestrate tools import -k python -f tools/medical_tools.py -r tools/requirements.txt
```

### Step 2: Import Agents
Registers the agent definitions.
```bash
orchestrate agents import -f agents/triage_agent.yaml
```

### Step 3: Deploy Agents
Makes the agent active and available for use.
```bash
orchestrate agents deploy -n "Triage Agent"
```

## 5. Multi-Agent Connection

*   **Collaborators**: Define sub-agents in the `collaborators` list of the supervisor agent.
*   **Routing**: The Supervisor's `instructions` are the routing logic. You tell the LLM *when* to call a collaborator.
*   **Execution**: The Orchestrate runtime handles the hand-off between agents automatically based on the Supervisor's decisions.

## 6. Best Practices

1.  **Docstrings**: Spend time on tool docstrings. They are the "UI" for the LLM.
2.  **Granularity**: specialized agents (Triage, Geo) are better than one giant agent.
3.  **Testing**: Test tools locally using the Python SDK before deploying.
4.  **Version Control**: Keep agent YAMLs and tool code in Git.
