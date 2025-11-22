# deploy_tools.py
from ibm_watsonx_orchestrate import OrchestrateClient
from tools import triage_patient_tool, find_hospitals_tool, allocate_patient_beds_tool
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ORCHESTRATE_API_KEY")
url = os.getenv("ORCHESTRATE_INSTANCE_URL")

if not api_key or not url:
    print("Error: ORCHESTRATE_API_KEY and ORCHESTRATE_INSTANCE_URL must be set in .env")
    exit(1)

client = OrchestrateClient(api_key=api_key, url=url)

# Register tools
tools = [triage_patient_tool, find_hospitals_tool, allocate_patient_beds_tool]
for tool in tools:
    try:
        client.deploy_tool(tool)
        print(f"Deployed: {tool.__name__}")
    except Exception as e:
        print(f"Failed to deploy {tool.__name__}: {e}")
