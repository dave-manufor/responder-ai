"""Session state management for multi-turn conversations."""
import uuid
import re
from typing import Dict, Optional, Tuple
from datetime import datetime
from database import get_database


class SessionManager:
    """
    Manages multi-turn conversation sessions for radio dispatches using MongoDB.
    
    Each session tracks:
    - Incident location
    - Casualty reports
    - Total patient count
    - Conversation history
    
    Sessions are stored in MongoDB 'sessions' collection for persistence.
    """
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.sessions
        
        # Create index on session_id for fast lookups
        try:
            self.collection.create_index("id", unique=True)
            self.collection.create_index("created_at")
            self.collection.create_index("status")
        except Exception as e:
            print(f"Note: Session index creation: {e}")
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new session in MongoDB.
        
        Args:
            session_id: Optional custom session ID, otherwise generates UUID
        
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Check if session already exists
        existing = self.collection.find_one({"id": session_id})
        if existing:
            return session_id  # Return existing session
        
        session_doc = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "location": None,
            "casualties": [],
            "total_casualties": 0,
            "transcripts": [],
            "status": "ACTIVE"
        }
        
        self.collection.insert_one(session_doc)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session by ID from MongoDB.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session document or None if not found
        """
        session = self.collection.find_one({"id": session_id}, {"_id": 0})
        return session
    
    
    def update_session(self, session_id: str, updates: Dict) -> Dict:
        """
        Update session with new data in MongoDB.
        
        Args:
            session_id: Session to update
            updates: Dictionary of fields to update
        
        Returns:
            Updated session
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        update_ops = {}
        
        # Handle location update
        if "location" in updates:
            update_ops["location"] = updates["location"]
        
        # Handle casualty addition (push to array)
        if "casualty" in updates:
            # Use $push to add to casualties array
            self.collection.update_one(
                {"id": session_id},
                {
                    "$push": {"casualties": updates["casualty"]},
                    "$inc": {"total_casualties": updates["casualty"].get("count", 0)}
                }
            )
        
        # Handle transcript addition (push to array)
        if "transcript" in updates:
            transcript_entry = {
                "text": updates["transcript"],
                "timestamp": datetime.utcnow().isoformat()
            }
            self.collection.update_one(
                {"id": session_id},
                {"$push": {"transcripts": transcript_entry}}
            )
        
        # Handle status update
        if "status" in updates:
            update_ops["status"] = updates["status"]
        
        # Apply remaining updates
        if update_ops:
            self.collection.update_one(
                {"id": session_id},
                {"$set": update_ops}
            )
        
        # Return updated session
        return self.get_session(session_id)
    
    
    def should_allocate(self, session_id: str, transcript: str) -> bool:
        """
        Determine if session is ready for bed allocation.
        
        Triggers allocation if:
        1. Keywords like "dispatch", "transport", "ambulance" detected
        2. Session has location
        3. Session has casualties
        
        Args:
            session_id: Session to check
            transcript: Latest transcript
        
        Returns:
            True if ready to allocate
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Check for allocation keywords
        keywords = ["dispatch", "transport", "ambulance", "requesting", "send"]
        has_keyword = any(kw in transcript.lower() for kw in keywords)
        
        # Check session prerequisites
        has_location = session.get("location") is not None
        has_casualties = session.get("total_casualties", 0) > 0
        
        return has_keyword and has_location and has_casualties
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from MongoDB.
        
        Args:
            session_id: Session to delete
        
        Returns:
            True if deleted, False if not found
        """
        result = self.collection.delete_one({"id": session_id})
        return result.deleted_count > 0
    
    def list_sessions(self, status: Optional[str] = None, limit: int = 100) -> list:
        """
        List sessions, optionally filtered by status.
        
        Args:
            status: Filter by status (ACTIVE/COMPLETED/ARCHIVED)
            limit: Maximum sessions to return
        
        Returns:
            List of session documents
        """
        query = {"status": status} if status else {}
        sessions = list(
            self.collection.find(query, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
        return sessions


# Entity extraction helpers

def extract_coordinates(text: str) -> Optional[Dict[str, float]]:
    """
    Extract coordinates from text.
    
    Patterns matched:
    - "-1.29, 36.82"
    - "coordinates -1.29, 36.82"
    - "lat -1.29 lon 36.82"
    
    Args:
        text: Input text
    
    Returns:
        {"lat": float, "lon": float} or None
    """
    # Pattern: decimal numbers separated by comma
    pattern = r"(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)"
    match = re.search(pattern, text)
    
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        
        # Validate ranges
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {"lat": lat, "lon": lon}
    
    # Alternative pattern: "lat X lon Y"
    lat_pattern = r"lat(?:itude)?\s+(-?\d+\.?\d*)"
    lon_pattern = r"lon(?:gitude)?\s+(-?\d+\.?\d*)"
    
    lat_match = re.search(lat_pattern, text, re.IGNORECASE)
    lon_match = re.search(lon_pattern, text, re.IGNORECASE)
    
    if lat_match and lon_match:
        lat, lon = float(lat_match.group(1)), float(lon_match.group(1))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {"lat": lat, "lon": lon}
    
    return None


def extract_casualty_count(text: str) -> Optional[int]:
    """
    Extract casualty/patient count from text.
    
    Patterns matched:
    - "20 casualties"
    - "15 patients"
    - "a dozen injured"
    - "a few wounded"
    
    Args:
        text: Input text
    
    Returns:
        Patient count or None
    """
    # Direct number patterns
    patterns = [
        r"(\d+)\s+(?:casualties|patients|injured|wounded|victims|people)",
        r"(?:casualties|patients|injured|wounded|victims|people)\s*:\s*(\d+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # Word-based numbers
    word_numbers = {
        "a few": 3,
        "several": 5,
        "a dozen": 12,
        "dozens": 24,
        "many": 10,
        "numerous": 15
    }
    
    text_lower = text.lower()
    for phrase, count in word_numbers.items():
        if phrase in text_lower:
            return count
    
    return None


def extract_entities(text: str) -> Dict:
    """
    Extract all entities from text.
    
    Returns:
        {
            "location": {"lat": float, "lon": float} or None,
            "casualty_count": int or None,
            "has_location_keyword": bool,
            "has_casualty_keyword": bool
        }
    """
    return {
        "location": extract_coordinates(text),
        "casualty_count": extract_casualty_count(text),
        "has_location_keyword": bool(re.search(
            r"\b(location|coordinates|position|at)\b", 
            text, 
            re.IGNORECASE
        )),
        "has_casualty_keyword": bool(re.search(
            r"\b(casualties|patients|injured|wounded|victims)\b",
            text,
            re.IGNORECASE
        ))
    }


# Global session manager instance
session_manager = SessionManager()
