"""
Respondr.ai Agent - Orchestrates multi-turn conversations and tool execution.

This agent coordinates the emergency dispatch workflow:
1. Receives radio transcripts
2. Extracts entities (location, casualty count)
3. Calls triage tool for classification
4. Triggers allocation when ready
5. Maintains session state across turns
"""
from typing import Dict, Optional
from sessions import session_manager, extract_entities
from agent_tools import triage_patient_tool, find_hospitals_tool, allocate_patient_beds_tool


class ResponderAgent:
    """
    Agent that orchestrates emergency dispatch workflow.
    
    Handles:
    - Multi-turn conversation tracking
    - Entity extraction from transcripts
    - Tool invocation (triage, find hospitals, allocate beds)
    - Conditional logic for allocation triggers
    """
    
    def __init__(self):
        self.session_manager = session_manager
    
    def process_transcript(
        self,
        transcript: str,
        session_id: str
    ) -> Dict:
        """
        Process a radio transcript and execute appropriate actions.
        
        Workflow:
        1. Extract entities (location, casualty count)
        2. Update session state
        3. Call triage if casualties mentioned
        4. Trigger allocation if ready
        
        Args:
            transcript: Radio transmission text
            session_id: Conversation session ID
        
        Returns:
            Agent response with action taken and next steps
        """
        # Ensure session exists
        session = self.session_manager.get_session(session_id)
        if not session:
            session_id = self.session_manager.create_session(session_id)
            session = self.session_manager.get_session(session_id)
        
        # Add transcript to history
        self.session_manager.update_session(session_id, {"transcript": transcript})
        
        # Extract entities
        entities = extract_entities(transcript)
        
        response = {
            "session_id": session_id,
            "transcript": transcript,
            "action": "acknowledged",
            "message": "Transmission received.",
            "session_state": None,
            "triage_result": None,
            "allocation_result": None
        }
        
        # STEP 1: Update location if found
        if entities["location"]:
            self.session_manager.update_session(
                session_id,
                {"location": entities["location"]}
            )
            response["action"] = "location_updated"
            response["message"] = f"Location confirmed: {entities['location']['lat']}, {entities['location']['lon']}. Go ahead."
        
        # STEP 2: Process casualty report if found
        if entities["casualty_count"]:
            # Call triage tool
            try:
                triage_result = triage_patient_tool(
                    transcript,
                    context={"location": session.get("location")}
                )
                
                # Update session with casualty info
                casualty_entry = {
                    "count": entities["casualty_count"],
                    "triage_color": triage_result["triage_color"],
                    "primary_injury": triage_result["primary_injury"],
                    "specialty_needed": triage_result["specialty_needed"],
                    "confidence": triage_result["confidence"]
                }
                
                self.session_manager.update_session(
                    session_id,
                    {"casualty": casualty_entry}
                )
                
                response["action"] = "casualty_reported"
                response["triage_result"] = triage_result
                response["message"] = (
                    f"Copy. {entities['casualty_count']} casualties triaged as "
                    f"{triage_result['triage_color']}. "
                    f"Primary injury: {triage_result['primary_injury']}. "
                    f"Standing by for transport request."
                )
                
            except Exception as e:
                response["action"] = "triage_error"
                response["message"] = f"Error processing casualty report: {str(e)}"
        
        # STEP 3: Check if allocation should be triggered
        session = self.session_manager.get_session(session_id)  # Refresh
        
        if self.session_manager.should_allocate(session_id, transcript):
            try:
                location = session["location"]
                total_casualties = session["total_casualties"]
                
                # Determine triage color (use most severe from session)
                triage_color = "RED"  # Default
                if session["casualties"]:
                    # Use the most severe triage color
                    colors_priority = {"BLACK": 4, "RED": 3, "YELLOW": 2, "GREEN": 1}
                    most_severe = max(
                        session["casualties"],
                        key=lambda c: colors_priority.get(c.get("triage_color", "RED"), 3)
                    )
                    triage_color = most_severe.get("triage_color", "RED")
                
                # Call allocation tool
                allocation_result = allocate_patient_beds_tool(
                    lat=location["lat"],
                    lon=location["lon"],
                    patient_count=total_casualties,
                    triage_color=triage_color
                )
                
                # Format response message
                if allocation_result["status"] == "SUCCESS":
                    allocations = allocation_result["plan"]
                    parts = [
                        f"{a['patients_sent']} to {a['hospital_name']} ({a['distance_km']:.1f}km)"
                        for a in allocations
                    ]
                    response["message"] = f"Dispatching: {', '.join(parts)}. Confirm."
                elif allocation_result["status"] == "PARTIAL":
                    allocated = sum(a["patients_sent"] for a in allocation_result["plan"])
                    response["message"] = (
                        f"Partial allocation: {allocated} patients assigned. "
                        f"{allocation_result['unallocated']} unallocated due to capacity limits."
                    )
                else:  # OVERFLOW
                    response["message"] = (
                        f"Unable to allocate {total_casualties} patients. "
                        f"No hospitals within range with sufficient capacity."
                    )
                
                response["action"] = "beds_allocated"
                response["allocation_result"] = allocation_result
                
                # Mark session as completed
                self.session_manager.update_session(session_id, {"status": "COMPLETED"})
                
            except Exception as e:
                response["action"] = "allocation_error"
                response["message"] = f"Error during allocation: {str(e)}"
        
        # Add current session state to response
        response["session_state"] = self.session_manager.get_session(session_id)
        
        return response
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current session state."""
        return self.session_manager.get_session(session_id)
    
    def reset_session(self, session_id: str) -> bool:
        """
        Reset a session (for testing/demo).
        
        Args:
            session_id: Session to reset
        
        Returns:
            True if reset successful
        """
        return self.session_manager.delete_session(session_id)


# Global agent instance
agent = ResponderAgent()
