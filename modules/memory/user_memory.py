"""
User Memory Store for Dynamic Pathway Generator
Wrapper around MemoryStore for specific user memory context operations
"""

from typing import Dict, List, Any, Optional
from .store import MemoryStore


class UserMemoryStore:
    """
    User memory interface for dynamic pathway generation
    """
    
    def __init__(self):
        self.memory_store = MemoryStore()
    
    async def get_user_medical_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's medical context and interaction history
        """
        if not user_id:
            return {"profile": {}, "medical_history": [], "interactions": []}
        
        context = await self.memory_store.get_user_context(user_id)
        
        # Extract medical-specific context
        profile = context.get("profile", {})
        recent_history = context.get("recent_history", [])
        
        # Filter for medical interactions
        medical_interactions = []
        for interaction in recent_history:
            response = interaction.get("response", {})
            if response.get("intent") in ["medical_query", "care_pathway", "document_analysis"]:
                medical_interactions.append({
                    "query": interaction["query"],
                    "condition": response.get("condition"),
                    "timestamp": interaction["timestamp"]
                })
        
        return {
            "profile": profile,
            "medical_history": profile.get("medical_history", []),
            "interactions": medical_interactions,
            "preferences": profile.get("preferences", {}),
            "allergies": profile.get("allergies", []),
            "medications": profile.get("current_medications", [])
        }
    
    async def store_interaction(self, interaction_data: Dict[str, Any]) -> None:
        """
        Store interaction data for machine learning
        """
        user_id = interaction_data.get("user_profile", {}).get("user_id")
        if not user_id:
            return
        
        # Extract key information for storage
        query = f"Medical pathway for {interaction_data.get('condition', 'unknown')}"
        response = {
            "intent": "care_pathway",
            "condition": interaction_data.get("condition"),
            "pathway_generated": True,
            "confidence": interaction_data.get("generated_pathway", {}).get("confidence", 0.0),
            "timestamp": interaction_data.get("timestamp")
        }
        
        await self.memory_store.update_session_history(user_id, query, response)
    
    async def update_user_medical_profile(self, user_id: str, medical_updates: Dict[str, Any]) -> None:
        """
        Update user's medical profile information
        """
        await self.memory_store.update_user_profile(user_id, medical_updates)
