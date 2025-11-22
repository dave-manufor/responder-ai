"""watsonx.ai integration for triage classification using START Protocol."""
from typing import Dict, Optional
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
import json
import re

from config import settings


class TriageService:
    """
    AI-powered triage classification using watsonx.ai and START Protocol.
    
    The START Protocol classifies casualties into 4 categories:
    - RED (Immediate): Life-threatening, treatable within 60 minutes
    - YELLOW (Delayed): Serious but stable, can wait hours
    - GREEN (Minor): Walking wounded, non-urgent
    - BLACK (Expectant): Deceased or unsalvageable
    """
    
    def __init__(self):
        """Initialize watsonx.ai model."""
        self.credentials = Credentials(
            url=settings.watsonx_url,
            api_key=settings.watsonx_api_key,
        )
        
        # Use Granite 3.0 8B Instruct - optimized for instruction following
        self.model = ModelInference(
            model_id="ibm/granite-3-8b-instruct",
            params={
                GenParams.DECODING_METHOD: "greedy",
                GenParams.MAX_NEW_TOKENS: 200,
                GenParams.MIN_NEW_TOKENS: 20,
                GenParams.TEMPERATURE: 0.1,  # Low temperature for consistent medical classification
                GenParams.REPETITION_PENALTY: 1.1
            },
            credentials=self.credentials,
            project_id=settings.watsonx_project_id
        )
    
    def classify_casualties(
        self,
        transcript: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Classify casualties using START Protocol.
        
        Args:
            transcript: Radio report describing casualties
            context: Optional session context (location, previous reports)
        
        Returns:
            {
                "triage_color": "RED" | "YELLOW" | "GREEN" | "BLACK",
                "primary_injury": str,
                "specialty_needed": str,
                "confidence": float,
                "reasoning": str
            }
        """
        context = context or {}
        
        # Build START Protocol prompt
        prompt = self._build_triage_prompt(transcript, context)
        
        try:
            # Generate response from watsonx.ai
            response = self.model.generate_text(prompt=prompt)
            
            # Parse JSON response
            result = self._parse_triage_response(response)
            
            return result
            
        except Exception as e:
            print(f"⚠️  Triage classification error: {e}")
            # Fallback to conservative RED classification
            return {
                "triage_color": "RED",
                "primary_injury": "Unknown",
                "specialty_needed": "General Trauma",
                "confidence": 0.5,
                "reasoning": f"Error during classification: {str(e)}. Defaulting to RED for safety."
            }
    
    def _build_triage_prompt(self, transcript: str, context: Dict) -> str:
        """Build START Protocol classification prompt."""
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
   - Not breathing after airway positioning → BLACK (not RED)
   - Respiratory rate > 30 breaths/min → RED
   - No radial pulse or capillary refill > 2 seconds → RED
   - Cannot follow simple commands (altered mental status) → RED
   - Severe bleeding, airway compromise, shock → RED

2. YELLOW (Delayed): Serious but stable
   - Fractures, moderate bleeding
   - Can wait several hours
   - Stable vital signs

3. GREEN (Minor): Walking wounded
   - Minor injuries
   - Can assist others
   - Non-urgent

4. BLACK (Expectant): Deceased or unsalvageable
   - Not breathing after airway positioning
   - Injuries incompatible with life

TASK:
Classify the casualties described in the report. Extract:
1. Triage Color (RED/YELLOW/GREEN/BLACK)
2. Primary Injury Type
3. Medical Specialty Needed
4. Brief Reasoning

OUTPUT FORMAT (JSON only):
{{
  "triage_color": "RED",
  "primary_injury": "Severe burns",
  "specialty_needed": "Burn Unit",
  "reasoning": "Burns with potential airway compromise require immediate care"
}}

Respond with ONLY the JSON object, no other text."""

        return prompt
    
    def _parse_triage_response(self, response: str) -> Dict:
        """Parse AI response and extract triage classification."""
        # Try to extract JSON from response
        try:
            # Find JSON object in response
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                
                # Validate required fields
                required = ["triage_color", "primary_injury", "specialty_needed"]
                if all(field in result for field in required):
                    # Add confidence based on response quality
                    result["confidence"] = 0.95
                    
                    # Ensure triage_color is valid
                    valid_colors = ["RED", "YELLOW", "GREEN", "BLACK"]
                    if result["triage_color"].upper() not in valid_colors:
                        result["triage_color"] = "RED"  # Default to safest
                    else:
                        result["triage_color"] = result["triage_color"].upper()
                    
                    return result
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
        
        # Fallback parsing: extract key information from text
        triage_color = "RED"  # Default to most urgent
        
        # Look for color keywords
        response_upper = response.upper()
        if "GREEN" in response_upper or "MINOR" in response_upper:
            triage_color = "GREEN"
        elif "YELLOW" in response_upper or "DELAYED" in response_upper:
            triage_color = "YELLOW"
        elif "BLACK" in response_upper or "DECEASED" in response_upper:
            triage_color = "BLACK"
        
        return {
            "triage_color": triage_color,
            "primary_injury": "Medical emergency",
            "specialty_needed": "General Trauma",
            "confidence": 0.7,
            "reasoning": "Parsed from unstructured response"
        }


# Global triage service instance
triage_service = TriageService()
