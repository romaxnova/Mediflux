"""
V2 Mediflux Orchestrator
Patient-centric care orchestration with intent-based routing
Lightweight, modular design for quick iteration and debugging
"""

import asyncio
from typing import Dict, List, Any, Optional
import json
import os
from .interpreter.intent_router import IntentRouter
from .memory.store import MemoryStore
from .reimbursement.simulator import ReimbursementSimulator
from .document_analyzer.handler import DocumentAnalyzer
from .care_pathway.advisor import CarePathwayAdvisor
from .data_hub.bdpm import BDPMClient
from .data_hub.annuaire import AnnuaireClient
from .data_hub.odisse import OdisseClient


class MedifluxOrchestrator:
    """
    Main orchestrator for V2 Mediflux
    Routes user intents to appropriate modules and manages user context
    """
    
    def __init__(self):
        self.intent_router = IntentRouter()
        self.memory_store = MemoryStore()
        self.reimbursement_simulator = ReimbursementSimulator()
        self.document_analyzer = DocumentAnalyzer()
        self.care_pathway_advisor = CarePathwayAdvisor()
        
        # Data clients
        self.bdpm_client = BDPMClient()
        self.annuaire_client = AnnuaireClient()
        self.odisse_client = OdisseClient()
        
    async def process_query(self, user_query: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Main entry point - process user query with context-aware routing
        
        Args:
            user_query: Natural language query from user
            user_id: User identifier for memory/context retrieval
            
        Returns:
            Structured response with results and metadata
        """
        try:
            print(f"[ORCHESTRATOR] Processing query: {user_query}")
            
            # Load user context from memory
            user_context = await self.memory_store.get_user_context(user_id)
            
            # Route query to appropriate intent
            intent_result = await self.intent_router.route_intent(user_query, user_context)
            
            # Execute intent-specific workflow
            response = await self._execute_intent_workflow(intent_result, user_context)
            
            # Update user memory with session data
            await self.memory_store.update_session_history(user_id, user_query, response)
            
            return {
                "success": True,
                "intent": intent_result["intent"],
                "confidence": intent_result["confidence"],
                "results": response,
                "user_context": user_context,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            print(f"[ORCHESTRATOR_ERROR] {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "intent": "error",
                "results": None
            }
    
    async def _execute_intent_workflow(self, intent_result: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the appropriate workflow based on detected intent
        """
        intent = intent_result["intent"]
        params = intent_result.get("params", {})
        
        if intent == "simulate_cost":
            return await self._handle_cost_simulation(params, user_context)
        elif intent == "analyze_document":
            return await self._handle_document_analysis(params, user_context)
        elif intent == "care_pathway":
            return await self._handle_care_pathway(params, user_context)
        elif intent == "medication_info":
            return await self._handle_medication_query(params, user_context)
        elif intent == "practitioner_search":
            return await self._handle_practitioner_search(params, user_context)
        else:
            # Fallback to general query handling
            return await self._handle_general_query(intent_result, user_context)
    
    async def _handle_cost_simulation(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reimbursement cost simulation requests"""
        try:
            # Enrich params with user profile data
            enriched_params = {**params}
            if "mutuelle" in user_context.get("profile", {}):
                enriched_params["mutuelle_type"] = user_context["profile"]["mutuelle"]
            if "pathology" in user_context.get("profile", {}):
                enriched_params["pathology"] = user_context["profile"]["pathology"]
            
            # Run simulation
            simulation_result = await self.reimbursement_simulator.simulate_costs(enriched_params)
            
            return {
                "type": "cost_simulation",
                "simulation": simulation_result,
                "context_used": bool(user_context.get("profile"))
            }
            
        except Exception as e:
            return {"error": f"Cost simulation failed: {str(e)}"}
    
    async def _handle_document_analysis(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document analysis requests"""
        try:
            document_path = params.get("document_path")
            document_type = params.get("document_type", "auto_detect")
            
            if not document_path:
                return {"error": "No document provided for analysis"}
            
            # Analyze document
            analysis_result = await self.document_analyzer.analyze_document(
                document_path, 
                document_type
            )
            
            # If analysis extracts mutuelle info, suggest updating user profile
            if "mutuelle_info" in analysis_result:
                profile_update_suggestion = {
                    "suggest_profile_update": True,
                    "extracted_mutuelle": analysis_result["mutuelle_info"]
                }
                analysis_result.update(profile_update_suggestion)
            
            return {
                "type": "document_analysis",
                "analysis": analysis_result
            }
            
        except Exception as e:
            return {"error": f"Document analysis failed: {str(e)}"}
    
    async def _handle_care_pathway(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle care pathway optimization requests"""
        try:
            # Enrich with user location and preferences
            enriched_params = {**params}
            if "location" in user_context.get("profile", {}):
                enriched_params["user_location"] = user_context["profile"]["location"]
            if "preferences" in user_context.get("profile", {}):
                enriched_params["preferences"] = user_context["profile"]["preferences"]
            
            # Get pathway recommendations
            pathway_result = await self.care_pathway_advisor.get_optimized_pathway(enriched_params)
            
            return {
                "type": "care_pathway",
                "pathway": pathway_result,
                "personalized": bool(user_context.get("profile"))
            }
            
        except Exception as e:
            return {"error": f"Care pathway analysis failed: {str(e)}"}
    
    async def _handle_medication_query(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle medication information requests"""
        try:
            medication_name = params.get("medication_name")
            search_type = params.get("search_type", "name")
            
            # Query BDPM for medication info
            medication_info = await self.bdpm_client.search_medication(
                query=medication_name,
                search_type=search_type
            )
            
            # If user has mutuelle info, add reimbursement context
            if user_context.get("profile", {}).get("mutuelle"):
                for med in medication_info.get("results", []):
                    if "presentations" in med:
                        # Add personalized reimbursement info
                        med["personalized_reimbursement"] = await self._get_personalized_reimbursement(
                            med["presentations"], 
                            user_context["profile"]["mutuelle"]
                        )
            
            return {
                "type": "medication_info",
                "medication_data": medication_info
            }
            
        except Exception as e:
            return {"error": f"Medication query failed: {str(e)}"}
    
    async def _handle_practitioner_search(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle practitioner/organization search requests"""
        try:
            # Use Annuaire Santé client for aggregated practitioner data
            search_result = await self.annuaire_client.search_practitioners(params)
            
            # Add care pathway context if available
            if user_context.get("profile", {}).get("pathology"):
                search_result["pathway_context"] = await self.care_pathway_advisor.get_pathway_context(
                    params.get("specialty"),
                    user_context["profile"]["pathology"]
                )
            
            return {
                "type": "practitioner_search",
                "search_results": search_result
            }
            
        except Exception as e:
            return {"error": f"Practitioner search failed: {str(e)}"}
    
    async def _handle_general_query(self, intent_result: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general queries that don't fit specific intents"""
        return {
            "type": "general_response",
            "message": "I understand you're asking about healthcare, but I need more specific information to help you better.",
            "suggestions": [
                "Ask about medication costs and reimbursement",
                "Upload a document for analysis (carte tiers payant, feuille de soins)",
                "Get care pathway recommendations for a specific condition"
            ]
        }
    
    async def _get_personalized_reimbursement(self, presentations: List[Dict], mutuelle_type: str) -> Dict[str, Any]:
        """Get personalized reimbursement info based on user's mutuelle"""
        # This would integrate with reimbursement simulator
        # For now, return a placeholder
        return {
            "mutuelle_coverage": "70%",  # Example
            "estimated_out_of_pocket": "€5.20",  # Example
            "note": f"Estimate based on {mutuelle_type} coverage"
        }
    
    async def upload_document(self, file_path: str, document_type: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Handle document upload and analysis
        """
        try:
            # Analyze the document
            analysis_result = await self.document_analyzer.analyze_document(file_path, document_type)
            
            # If it's a carte tiers payant, update user profile
            if document_type == "carte_tiers_payant" and "mutuelle_info" in analysis_result:
                await self.memory_store.update_user_profile(
                    user_id, 
                    {"mutuelle": analysis_result["mutuelle_info"]}
                )
            
            return {
                "success": True,
                "analysis": analysis_result,
                "profile_updated": document_type == "carte_tiers_payant"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Document upload failed: {str(e)}"
            }
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile information
        """
        try:
            await self.memory_store.update_user_profile(user_id, profile_data)
            return {
                "success": True,
                "message": "Profile updated successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Profile update failed: {str(e)}"
            }
