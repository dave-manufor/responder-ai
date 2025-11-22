"""Triage tool for casualty classification - production ready."""
from typing import Dict, Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import json
import re
import os


@tool
def triage_patient_tool(transcript: str, context: Dict) -> Dict:
    """Classify casualties using START Protocol via watsonx.ai.

    Analyzes casualty reports and assigns triage categories using the START Protocol.

    Args:
        transcript (str): Radio transmission describing casualties.
        context (dict): Session state containing location and casualty history.

    Returns:
        dict: Triage classification with color, injury, and specialty.
    """
    # Get watsonx credentials from environment
    watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    watsonx_api_key = os.getenv("WATSONX_API_KEY")
    watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
    
    if not watsonx_api_key or not watsonx_project_id:
        return {
            "triage_color": "RED",
            "primary_injury": "Unknown",
            "specialty_needed": "General Trauma",
            "confidence": 0.5,
            "reasoning": "Missing watsonx credentials - defaulting to RED for safety"
        }
    
    try:
        # Initialize watsonx.ai
        credentials = Credentials(url=watsonx_url, api_key=watsonx_api_key)
        model = ModelInference(
            model_id="ibm/granite-3-8b-instruct",
            params={
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 200,
                GenParams.MIN_NEW_TOKENS: 20,
                GenParams.TEMPERATURE: 0.1,
                GenParams.REPETITION_PENALTY: 1.1
            },
            credentials=credentials,
            project_id=watsonx_project_id
        )
        
        # Build prompt
        location_str = "Unknown location"
        if context.get("location"):
            loc = context["location"]
            location_str = f"Coordinates: {loc.get('lat')}, {loc.get('lon')}"
        
        prompt = f"""You are an Emergency Medical Dispatch AI following the START Protocol for mass casualty triage.

CONTEXT:
- Location: {location_str}
- Report: {transcript}

START PROTOCOL RULES:
1. RED (Immediate): Life-threatening but treatable
   - Respiratory rate > 30 breaths/min → RED
   - No radial pulse or capillary refill > 2 seconds → RED
   - Cannot follow simple commands → RED
   - Severe bleeding, airway compromise, shock → RED

2. YELLOW (Delayed): Serious but stable
   - Fractures, moderate bleeding
   - Stable vital signs

3. GREEN (Minor): Walking wounded
   - Minor injuries, non-urgent

4. BLACK (Expectant): Deceased or unsalvageable

OUTPUT FORMAT (JSON only):
{{
  "triage_color": "RED",
  "primary_injury": "Severe burns",
  "specialty_needed": "Burn Unit",
  "reasoning": "Brief clinical reasoning"
}}

Respond with ONLY the JSON object, no other text."""

        # Generate response
        response = model.generate_text(prompt=prompt)
        
        # Parse JSON
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            result["confidence"] = 0.95
            result["triage_color"] = result["triage_color"].upper()
            return result
            
    except Exception as e:
        print(f"Triage error: {e}")
    
    # Fallback
    return {
        "triage_color": "RED",
        "primary_injury": "Medical emergency",
        "specialty_needed": "General Trauma",
        "confidence": 0.7,
        "reasoning": "Error during classification - defaulting to RED for safety"
    }
