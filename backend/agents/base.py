"""Base Agent class for multi-agent system."""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    description: str
    model_id: str = "ibm/granite-3-8b-instruct"
    tools: List[str] = []
    collaborators: List[str] = []
    system_prompt: str


class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
    
    async def process(self, input_text: str, context: Dict) -> Dict:
        """
        Process input and return response.
        Must be implemented by subclasses.
        """
        raise NotImplementedError
    
    def get_tool_definitions(self) -> List[Dict]:
        """Return tool definitions for this agent."""
        # In a real implementation, this would return the JSON schema for tools
        return []
