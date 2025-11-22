"""
Orchestration Adapter - Interface for interacting with the Supervisor Agent.

Handles:
1. Production: Calls the deployed Supervisor Agent via watsonx Orchestrate SDK.
2. Local: Uses a local Python implementation of the Supervisor logic.
"""
import os
from typing import Dict, Optional
from config import settings

# Import tools for local mode
from tools.session_tool import manage_session_tool
from tools.triage_tool import triage_patient_tool
from tools.geo_tool import find_hospitals_tool
from tools.bed_tool import allocate_patient_beds_tool
from sessions import extract_entities

class OrchestrationAdapter:
    def __init__(self, mode: str = None):
        self.mode = mode or settings.orchestrate_mode
        print(f"🔧 Orchestration Adapter initialized in {self.mode} mode")
        
        if self.mode == "production":
            # Initialize Orchestrate SDK client here if needed
            pass

    async def process_transcript(self, transcript: str, session_id: str) -> Dict:
        """
        Process a transcript through the Supervisor Agent.
        """
        if self.mode == "production":
            return await self._process_cloud(transcript, session_id)
        else:
            return await self._process_local(transcript, session_id)

    async def _process_cloud(self, transcript: str, session_id: str) -> Dict:
        """
        Call the deployed Supervisor Agent in watsonx Orchestrate.
        """
        if not settings.orchestrate_agent_id or not settings.orchestrate_api_key:
            return {
                "session_id": session_id,
                "transcript": transcript,
                "message": "Error: ORCHESTRATE_AGENT_ID or API_KEY not configured.",
                "action": "error",
                "mode": "production"
            }

        try:
            # Import here to avoid hard dependency if not in production mode
            from ibm_watsonx_orchestrate import OrchestrateClient
            
            client = OrchestrateClient(
                api_key=settings.orchestrate_api_key,
                url=settings.orchestrate_instance_url
            )
            
            # Run in executor to avoid blocking event loop
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: client.agents.run(
                    agent_id=settings.orchestrate_agent_id,
                    input={
                        "text": transcript,
                        "session_id": session_id
                    }
                )
            )
            
            # Parse response from Agent
            # Expected format depends on Agent's output schema
            # Assuming it returns a text response
            agent_text = response.get("output", {}).get("text", "No response from agent.")
            
            return {
                "session_id": session_id,
                "transcript": transcript,
                "message": agent_text,
                "action": "processed",
                "mode": "production"
            }
            
        except Exception as e:
            print(f"Cloud Orchestrate Error: {e}")
            return {
                "session_id": session_id,
                "transcript": transcript,
                "message": "Fallback: Error communicating with Cloud Agent. Switching to local.",
                "action": "fallback",
                "mode": "production_fallback"
            }

    async def _process_local(self, transcript: str, session_id: str) -> Dict:
        """
        Local implementation of Supervisor Agent logic (mirroring supervisor.yaml).
        """
        # 1. Check State
        session = manage_session_tool(action="get", session_id=session_id)
        if session.get("status") == "COMPLETED":
            return {
                "session_id": session_id,
                "transcript": transcript,
                "message": "Session already completed.",
                "action": "completed",
                "mode": "local"
            }

        # 2. Entity Extraction (Simulating LLM extraction)
        entities = extract_entities(transcript)
        response_message = ""
        action_taken = "processed"

        # 3. Extract & Delegate
        # Location -> Geo Agent
        if entities["location"]:
            # Delegate to Geo Tool (Simulating Geo Agent)
            hospitals = find_hospitals_tool(
                lat=entities["location"]["lat"],
                lon=entities["location"]["lon"]
            )
            # Update Session
            manage_session_tool(
                action="update", 
                session_id=session_id, 
                updates={"location": entities["location"]}
            )
            if hospitals:
                response_message += f"Found {len(hospitals)} hospitals nearby. "
            else:
                response_message += "No hospitals found nearby. "

        # Casualties -> Triage Agent
        if entities["casualty_count"] or entities["has_casualty_keyword"]:
            # Delegate to Triage Tool (Simulating Triage Agent)
            # We pass the raw transcript to the tool
            triage_result = triage_patient_tool(transcript=transcript, context=session)
            
            # Update Session
            casualty_data = {
                "count": entities["casualty_count"] or 1, # Default to 1 if not parsed
                "triage_color": triage_result.get("triage_color", "RED"),
                "description": transcript
            }
            manage_session_tool(
                action="update",
                session_id=session_id,
                updates={"casualty": casualty_data}
            )
            response_message += f"Recorded {casualty_data['count']} casualties ({casualty_data['triage_color']}). "

        # 4. Handle Transport Requests
        keywords = ["transport", "ambulance", "dispatch", "beds", "send"]
        is_transport_request = any(kw in transcript.lower() for kw in keywords)
        
        if is_transport_request:
            # Refresh session state
            session = manage_session_tool(action="get", session_id=session_id)
            has_location = session.get("location") is not None
            has_casualties = session.get("total_casualties", 0) > 0
            
            if not has_location or not has_casualties:
                missing = []
                if not has_location: missing.append("location")
                if not has_casualties: missing.append("casualties")
                return {
                    "session_id": session_id,
                    "transcript": transcript,
                    "message": f"Copy, I need the {' and '.join(missing)} before I can dispatch.",
                    "action": "request_info",
                    "mode": "local"
                }
            else:
                # Delegate to Bed Agent
                # Get latest casualty info for triage color
                last_casualty = session["casualties"][-1] if session["casualties"] else {}
                triage_color = last_casualty.get("triage_color", "RED")
                
                allocation = allocate_patient_beds_tool(
                    lat=session["location"]["lat"],
                    lon=session["location"]["lon"],
                    patient_count=session["total_casualties"],
                    triage_color=triage_color
                )
                
                # Complete Session
                manage_session_tool(action="complete", session_id=session_id)
                
                return {
                    "session_id": session_id,
                    "transcript": transcript,
                    "message": f"Dispatching resources. {allocation['message']}",
                    "action": "dispatch",
                    "mode": "local",
                    "allocation_plan": allocation.get("plan")
                }

        # 5. Standard Acknowledgement
        if not response_message:
            response_message = "Copy that. Standing by."
            
        return {
            "session_id": session_id,
            "transcript": transcript,
            "message": response_message.strip(),
            "action": action_taken,
            "mode": "local"
        }

# Global instance
adapter = OrchestrationAdapter()
