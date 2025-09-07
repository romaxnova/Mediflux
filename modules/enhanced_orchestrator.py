"""
Enhanced Mediflux Orchestrator - LangChain Integration
Seamlessly integrates the new LangChain system while maintaining API compatibility
"""

import asyncio
from typing import Dict, List, Any, Optional
import json
import os
import logging
from datetime import datetime

# Import existing modules for backward compatibility
from .interpreter.intent_router import IntentRouter
from .memory.store import MemoryStore
from .reimbursement.simulator import ReimbursementSimulator
from .document_analyzer.handler import DocumentAnalyzer
from .care_pathway.advisor import CarePathwayAdvisor
from .data_hub.bdpm import BDPMClient
from .data_hub.annuaire import AnnuaireClient
from .data_hub.odisse import OdisseClient
from .ai.response_generator import AIResponseGenerator

# Import new LangChain components
from .langchain_orchestrator import LangChainOrchestrator
from .specialized_agents import AgentOrchestrator


class EnhancedMedifluxOrchestrator:
    """
    Enhanced orchestrator that integrates LangChain while maintaining backward compatibility
    Provides intelligent routing and improved healthcare query processing
    """
    
    def __init__(self, use_langchain: bool = True):
        self.logger = logging.getLogger(__name__)
        self.use_langchain = use_langchain
        
        # Initialize new LangChain components
        if self.use_langchain:
            try:
                self.langchain_orchestrator = LangChainOrchestrator()
                self.agent_orchestrator = AgentOrchestrator()
                self.logger.info("✅ LangChain components initialized successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ LangChain initialization failed: {e}")
                self.use_langchain = False
        
        # Initialize existing components for backward compatibility
        self.intent_router = IntentRouter()
        self.memory_store = MemoryStore()
        self.reimbursement_simulator = ReimbursementSimulator()
        self.document_analyzer = DocumentAnalyzer()
        self.care_pathway_advisor = CarePathwayAdvisor()
        self.ai_response_generator = AIResponseGenerator()
        
        # Data clients
        self.bdpm_client = BDPMClient()
        self.annuaire_client = AnnuaireClient()
        self.odisse_client = OdisseClient()
        
        self.logger.info(f"Enhanced orchestrator initialized (LangChain: {'enabled' if self.use_langchain else 'disabled'})")
    
    async def process_query(self, user_query: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Main entry point - intelligently route to LangChain or legacy system
        """
        try:
            self.logger.info(f"[ENHANCED_ORCHESTRATOR] Processing query: {user_query}")
            
            # Load user context from memory
            user_context = await self.memory_store.get_user_context(user_id)
            
            # Try LangChain system first if available
            if self.use_langchain and await self._should_use_langchain(user_query, user_context):
                return await self._process_with_langchain(user_query, user_id, user_context)
            else:
                # Fallback to legacy system
                return await self._process_with_legacy(user_query, user_id, user_context)
                
        except Exception as e:
            self.logger.error(f"[ENHANCED_ORCHESTRATOR_ERROR] {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "intent": "error",
                "results": None,
                "system_used": "error"
            }
    
    async def _should_use_langchain(self, user_query: str, user_context: Dict[str, Any]) -> bool:
        """
        Determine if query should be processed by LangChain system
        """
        # For now, use LangChain for all text queries
        # In the future, this could be more sophisticated
        return len(user_query.strip()) > 0 and self.use_langchain
    
    async def _process_with_langchain(self, user_query: str, user_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process query using the new LangChain system
        """
        try:
            self.logger.info("🚀 Using LangChain system for query processing")
            
            # Route query through intelligent agent system
            agent_result = await self.agent_orchestrator.route_query(user_query)
            
            if not agent_result.get('success', False):
                # If agent routing fails, fallback to legacy
                self.logger.warning("Agent routing failed, falling back to legacy system")
                return await self._process_with_legacy(user_query, user_id, user_context)
            
            # Extract information from agent result
            agent_used = agent_result.get('agent_used', 'unknown')
            agent_response = agent_result.get('result', {})
            
            # Generate enhanced AI response using LangChain
            try:
                langchain_response = await self.langchain_orchestrator.process_query(
                    user_query, user_id=user_id
                )
                ai_response = self._extract_response_text(langchain_response)
            except Exception as lc_error:
                self.logger.warning(f"LangChain response generation failed: {lc_error}")
                ai_response = self._generate_fallback_response(agent_response, agent_used)
            
            # Update user memory with session data
            await self.memory_store.update_session_history(user_id, user_query, agent_result)
            
            # Convert to API-compatible format
            return {
                "success": True,
                "intent": self._map_agent_to_intent(agent_used),
                "confidence": 0.9,  # High confidence for LangChain routing
                "response": ai_response,
                "results": self._enhance_results_with_context(agent_response, user_context),
                "user_context": user_context,
                "system_used": "langchain",
                "agent_used": agent_used,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"LangChain processing failed: {e}")
            # Graceful fallback to legacy system
            return await self._process_with_legacy(user_query, user_id, user_context)
    
    async def _process_with_legacy(self, user_query: str, user_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process query using the legacy system (backward compatibility)
        """
        try:
            self.logger.info("🔄 Using legacy system for query processing")
            
            # Route query to appropriate intent (legacy)
            intent_result = await self.intent_router.route_intent(user_query, user_context)
            
            # Execute intent-specific workflow (legacy)
            response = await self._execute_intent_workflow(intent_result, user_context)
            
            # Generate AI response based on results (legacy)
            ai_response = await self.ai_response_generator.generate_response(
                user_query=user_query,
                intent=intent_result["intent"],
                orchestrator_results=response,
                user_context=user_context
            )
            
            # Update user memory with session data
            await self.memory_store.update_session_history(user_id, user_query, response)
            
            return {
                "success": True,
                "intent": intent_result["intent"],
                "confidence": intent_result["confidence"],
                "response": ai_response,
                "results": response,
                "user_context": user_context,
                "system_used": "legacy",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Legacy processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "intent": "error",
                "results": None,
                "system_used": "error"
            }
    
    def _map_agent_to_intent(self, agent_type: str) -> str:
        """Map LangChain agent types to legacy intent types for API compatibility"""
        mapping = {
            "medication": "medication_info",
            "pathway": "care_pathway", 
            "reimbursement": "simulate_cost",
            "document_analyzer": "analyze_document"
        }
        return mapping.get(agent_type, "general_query")
    
    def _extract_response_text(self, langchain_response: Dict[str, Any]) -> str:
        """Extract readable response text from LangChain result"""
        if isinstance(langchain_response, dict):
            # Try multiple response fields
            for field in ["response", "output", "result", "answer"]:
                if field in langchain_response and langchain_response[field]:
                    response_text = str(langchain_response[field]).strip()
                    if response_text and len(response_text) > 10:  # Avoid empty/short responses
                        return response_text
        
        # If no valid response found, return fallback
        return "Réponse générée par le système LangChain"
    
    def _generate_fallback_response(self, agent_response: Dict[str, Any], agent_used: str) -> str:
        """Generate fallback response when LangChain response fails"""
        if isinstance(agent_response, dict):
            response_text = agent_response.get('response', '')
            if response_text:
                return response_text
        
        # Agent-specific fallback responses
        agent_responses = {
            "medication": "J'ai analysé votre demande concernant les médicaments. Les informations sont disponibles via la base BDPM.",
            "pathway": "J'ai examiné votre parcours de soins. Des recommandations personnalisées sont disponibles.",
            "reimbursement": "J'ai calculé les informations de remboursement selon votre profil."
        }
        
        return agent_responses.get(agent_used, "Votre demande a été traitée avec succès.")
    
    def _enhance_results_with_context(self, agent_response: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance agent response with user context for richer results"""
        enhanced = dict(agent_response) if isinstance(agent_response, dict) else {"response": str(agent_response)}
        
        # Check if we have meaningful user context
        has_profile = bool(user_context.get("profile")) and len(user_context.get("profile", {})) > 0
        has_history = bool(user_context.get("recent_history")) and len(user_context.get("recent_history", [])) > 0
        
        # Add user context indicators
        enhanced["personalized"] = has_profile
        enhanced["context_available"] = has_history
        
        # If we have user profile, enhance the response
        if has_profile:
            profile = user_context["profile"]
            enhanced["user_profile_used"] = {
                "mutuelle": profile.get("mutuelle"),
                "location": profile.get("location"), 
                "pathology": profile.get("pathology")
            }
        
        # If we have conversation history, add context awareness
        if has_history:
            recent_queries = [item.get("query", "") for item in user_context["recent_history"][-3:]]
            enhanced["conversation_context"] = {
                "previous_queries": recent_queries,
                "session_length": len(user_context["recent_history"])
            }
        
        return enhanced
    
    # Legacy methods for backward compatibility
    async def _execute_intent_workflow(self, intent_result: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the appropriate workflow based on detected intent (legacy)"""
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
            return await self._handle_general_query(intent_result, user_context)
    
    async def _handle_cost_simulation(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reimbursement cost simulation requests (legacy)"""
        try:
            enriched_params = {**params}
            if "mutuelle" in user_context.get("profile", {}):
                enriched_params["mutuelle_type"] = user_context["profile"]["mutuelle"]
            if "pathology" in user_context.get("profile", {}):
                enriched_params["pathology"] = user_context["profile"]["pathology"]
            
            simulation_result = await self.reimbursement_simulator.simulate_costs(enriched_params)
            
            return {
                "type": "cost_simulation",
                "simulation": simulation_result,
                "context_used": bool(user_context.get("profile"))
            }
        except Exception as e:
            return {"error": f"Cost simulation failed: {str(e)}"}
    
    async def _handle_document_analysis(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document analysis requests (legacy)"""
        try:
            document_path = params.get("document_path")
            document_type = params.get("document_type", "auto_detect")
            
            if not document_path:
                return {"error": "No document provided for analysis"}
            
            analysis_result = await self.document_analyzer.analyze_document(document_path, document_type)
            
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
        """Handle care pathway optimization requests (legacy)"""
        try:
            enriched_params = {**params}
            if "location" in user_context.get("profile", {}):
                enriched_params["user_location"] = user_context["profile"]["location"]
            if "preferences" in user_context.get("profile", {}):
                enriched_params["preferences"] = user_context["profile"]["preferences"]
            
            pathway_result = await self.care_pathway_advisor.get_optimized_pathway(enriched_params)
            
            return {
                "type": "care_pathway",
                "pathway": pathway_result,
                "personalized": bool(user_context.get("profile"))
            }
        except Exception as e:
            return {"error": f"Care pathway analysis failed: {str(e)}"}
    
    async def _handle_medication_query(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle medication information requests (legacy)"""
        try:
            medication_name = params.get("medication_name")
            search_type = params.get("search_type", "name")
            
            medication_info = await self.bdpm_client.search_medication(
                query=medication_name,
                search_type=search_type
            )
            
            if user_context.get("profile", {}).get("mutuelle"):
                for med in medication_info.get("results", []):
                    if "presentations" in med:
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
        """Handle practitioner/organization search requests (legacy)"""
        try:
            search_result = await self.annuaire_client.search_practitioners(params)
            
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
        """Handle general queries that don't fit specific intents (legacy)"""
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
        """Get personalized reimbursement info based on user's mutuelle (legacy)"""
        return {
            "mutuelle_coverage": "70%",
            "estimated_out_of_pocket": "€5.20",
            "note": f"Estimate based on {mutuelle_type} coverage"
        }
    
    # Public methods for API compatibility
    async def upload_document(self, file_path: str, document_type: str, user_id: str = "default") -> Dict[str, Any]:
        """Handle document upload and analysis"""
        try:
            analysis_result = await self.document_analyzer.analyze_document(file_path, document_type)
            
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
        """Update user profile information"""
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
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of both systems for monitoring"""
        status = {
            "enhanced_orchestrator": "active",
            "langchain_enabled": self.use_langchain,
            "legacy_fallback": "active",
            "timestamp": datetime.now().isoformat()
        }
        
        if self.use_langchain:
            try:
                agent_status = self.agent_orchestrator.get_agent_status()
                status["langchain_agents"] = agent_status
            except Exception as e:
                status["langchain_error"] = str(e)
        
        return status


# Create alias for backward compatibility
MedifluxOrchestrator = EnhancedMedifluxOrchestrator
