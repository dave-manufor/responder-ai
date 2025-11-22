"""Session manager tool for Supervisor Agent."""
from typing import Dict, Optional, List
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from ibm_watsonx_orchestrate.agent_builder.connections import ExpectedCredentials, ConnectionType
from ibm_watsonx_orchestrate.run import connections
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import os
import uuid

DB_CONNECTION_ID = "mongodb_connection"

@tool(
    permission=ToolPermission.READ_WRITE,
    expected_credentials=[ExpectedCredentials(app_id=DB_CONNECTION_ID, type=ConnectionType.KEY_VALUE)]
)
def manage_session_tool(
    action: str,
    session_id: str,
    updates: Optional[Dict] = None
) -> Dict:
    """Manage conversation session state for emergency response.

    Allows the Supervisor Agent to retrieve, update, or complete session state.

    Args:
        action (str): The action to perform (get, update, complete).
        session_id (str): Unique identifier for the session.
        updates (Dict, optional): Data to update (location, casualty, transcript). Defaults to None.

    Returns:
        Dict: The updated or retrieved session object.
    """
    creds = connections.key_value(DB_CONNECTION_ID)
    # mongodb_uri = creds.get("MONGODB_URI")

    # Hard code for hackerthon
    mongodb_uri = "mongodb+srv://responder-ai:NwxHmv7xQXeQP8ew@cluster0.gtj199a.mongodb.net/retryWrites=true&w=majority"
    if not mongodb_uri:
        return {"error": "MongoDB URI not configured"}
    
    try:
        client = MongoClient(
            mongodb_uri,
            server_api=ServerApi('1'),
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        db = client.respondr_hospitals
        collection = db.sessions
        
        # Ensure session exists
        session = collection.find_one({"id": session_id}, {"_id": 0})
        
        if not session:
            if action == "get":
                # Create new if getting non-existent
                session = {
                    "id": session_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "location": None,
                    "casualties": [],
                    "total_casualties": 0,
                    "transcripts": [],
                    "status": "ACTIVE"
                }
                collection.insert_one(session)
                del session["_id"]
            else:
                return {"error": f"Session {session_id} not found"}
        
        if action == "get":
            return session
            
        elif action == "complete":
            collection.update_one(
                {"id": session_id},
                {"$set": {"status": "COMPLETED"}}
            )
            session["status"] = "COMPLETED"
            return session
            
        elif action == "update" and updates:
            update_ops = {}
            push_ops = {}
            inc_ops = {}
            
            if "location" in updates:
                update_ops["location"] = updates["location"]
                
            if "casualty" in updates:
                push_ops["casualties"] = updates["casualty"]
                inc_ops["total_casualties"] = updates["casualty"].get("count", 0)
                
            if "transcript" in updates:
                push_ops["transcripts"] = {
                    "text": updates["transcript"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            mongo_update = {}
            if update_ops: mongo_update["$set"] = update_ops
            if push_ops: mongo_update["$push"] = push_ops
            if inc_ops: mongo_update["$inc"] = inc_ops
            
            if mongo_update:
                collection.update_one({"id": session_id}, mongo_update)
                
            return collection.find_one({"id": session_id}, {"_id": 0})
            
        return {"error": "Invalid action or missing updates"}
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        if 'client' in locals():
            client.close()
