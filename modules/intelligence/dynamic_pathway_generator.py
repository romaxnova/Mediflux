"""
Dynamic AI-Powered Pathway Generator
Generates personalized care pathways using AI + real-time evidence synthesis
No hardcoded pathways - pure intelligence
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiohttp
from dataclasses import dataclass

from ..memory.user_memory import UserMemoryStore
from .evidence_retriever import EvidenceRetriever
from ..ai.medical_reasoning_engine import MedicalReasoningEngine


@dataclass
class PathwayContext:
    """Context for pathway generation"""
    condition: str
    patient_profile: Dict[str, Any]
    user_preferences: Dict[str, Any]
    medical_history: List[Dict[str, Any]]
    regional_context: Dict[str, Any]
    urgency_level: str = "standard"


class DynamicPathwayGenerator:
    """
    Generates personalized care pathways using AI reasoning + real-time evidence
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evidence_retriever = EvidenceRetriever()
        self.reasoning_engine = MedicalReasoningEngine()
        self.memory_store = UserMemoryStore()
        
    async def generate_personalized_pathway(
        self, 
        context: PathwayContext
    ) -> Dict[str, Any]:
        """
        Generate a completely personalized care pathway using AI reasoning
        """
        try:
            # 1. Retrieve relevant evidence from multiple sources
            evidence = await self._gather_evidence(context.condition)
            
            # 2. Get user's medical context and preferences
            user_context = await self._build_user_context(context)
            
            # 3. Use AI to reason about optimal pathway
            pathway = await self._generate_ai_pathway(evidence, user_context)
            
            # 4. Personalize based on user profile and history
            personalized_pathway = await self._personalize_pathway(pathway, context)
            
            # 5. Add real-time regional context
            regional_pathway = await self._add_regional_context(personalized_pathway, context)
            
            # 6. Generate dynamic confidence and quality metrics
            quality_assessment = await self._assess_pathway_quality(regional_pathway, context)
            
            return {
                "success": True,
                "pathway": regional_pathway,
                "confidence": quality_assessment["confidence"],
                "evidence_quality": quality_assessment["evidence_quality"],
                "personalization_score": quality_assessment["personalization"],
                "generated_at": datetime.now().isoformat(),
                "reasoning_trace": quality_assessment["reasoning_trace"]
            }
            
        except Exception as e:
            self.logger.error(f"Dynamic pathway generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_available": True
            }
    
    async def _gather_evidence(self, condition: str) -> Dict[str, Any]:
        """
        Dynamically retrieve evidence from multiple medical sources
        """
        # Get evidence from multiple sources
        evidence_sources = await asyncio.gather(
            self.evidence_retriever.get_has_guidelines(condition),
            self.evidence_retriever.get_international_guidelines(condition),
            self.evidence_retriever.get_recent_research(condition),
            self.evidence_retriever.get_medication_database(condition),
            return_exceptions=True
        )
        
        # Synthesize evidence with quality scoring
        synthesized_evidence = await self.evidence_retriever.synthesize_evidence(
            condition, evidence_sources
        )
        
        return synthesized_evidence
    
    async def _build_user_context(self, context: PathwayContext) -> Dict[str, Any]:
        """
        Build comprehensive user context from memory and profile
        """
        # Get user's medical history and preferences
        user_memory = await self.memory_store.get_user_medical_context(
            context.patient_profile.get("user_id")
        )
        
        # Analyze user patterns and preferences
        user_analysis = await self.reasoning_engine.analyze_user_patterns(
            medical_history=context.medical_history,
            preferences=context.user_preferences,
            past_interactions=user_memory
        )
        
        return {
            "profile": context.patient_profile,
            "history": context.medical_history,
            "preferences": context.user_preferences,
            "patterns": user_analysis,
            "regional_context": context.regional_context
        }
    
    async def _generate_ai_pathway(
        self, 
        evidence: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI reasoning to generate optimal pathway based on evidence + user context
        """
        # Create reasoning prompt for medical AI
        reasoning_prompt = self._build_medical_reasoning_prompt(evidence, user_context)
        
        # Use AI to reason about optimal pathway
        ai_pathway = await self.reasoning_engine.reason_about_pathway(
            prompt=reasoning_prompt,
            evidence=evidence,
            user_context=user_context
        )
        
        return ai_pathway
    
    async def _personalize_pathway(
        self, 
        pathway: Dict[str, Any], 
        context: PathwayContext
    ) -> Dict[str, Any]:
        """
        Personalize pathway based on user's specific situation
        """
        # Analyze user preferences and constraints
        personalization_factors = {
            "urgency_preference": context.user_preferences.get("urgency", "standard"),
            "cost_sensitivity": context.user_preferences.get("cost_priority", "balanced"),
            "provider_preference": context.user_preferences.get("provider_type", "any"),
            "medical_history": context.medical_history,
            "contraindications": await self._check_contraindications(context)
        }
        
        # Use AI to adapt pathway
        personalized = await self.reasoning_engine.personalize_pathway(
            pathway, personalization_factors
        )
        
        return personalized
    
    async def _add_regional_context(
        self, 
        pathway: Dict[str, Any], 
        context: PathwayContext
    ) -> Dict[str, Any]:
        """
        Add real-time regional data (wait times, availability, costs)
        """
        # Get real-time regional data
        regional_data = await self.evidence_retriever.get_regional_healthcare_data(
            region=context.regional_context.get("location", "paris"),
            providers_needed=pathway.get("provider_types", [])
        )
        
        # Update pathway with real regional context
        regionalized_pathway = await self.reasoning_engine.adapt_to_region(
            pathway, regional_data
        )
        
        return regionalized_pathway
    
    async def _assess_pathway_quality(
        self, 
        pathway: Dict[str, Any], 
        context: PathwayContext
    ) -> Dict[str, Any]:
        """
        Generate dynamic quality assessment and confidence scores
        """
        quality_metrics = await self.reasoning_engine.assess_pathway_quality(
            pathway=pathway,
            evidence_quality=pathway.get("evidence_quality", {}),
            personalization_factors=context.patient_profile,
            regional_accuracy=pathway.get("regional_context", {})
        )
        
        return quality_metrics
    
    def _build_medical_reasoning_prompt(
        self, 
        evidence: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> str:
        """
        Build sophisticated prompt for medical AI reasoning
        """
        return f"""
        You are an expert medical AI assistant specializing in evidence-based care pathway optimization.
        
        PATIENT CONTEXT:
        - Condition: {user_context.get('profile', {}).get('condition', 'Unknown')}
        - Demographics: {json.dumps(user_context.get('profile', {}), indent=2)}
        - Medical History: {json.dumps(user_context.get('history', []), indent=2)}
        - Preferences: {json.dumps(user_context.get('preferences', {}), indent=2)}
        
        AVAILABLE EVIDENCE:
        {json.dumps(evidence, indent=2)}
        
        TASK: Generate the optimal, personalized care pathway that:
        1. Follows the highest quality evidence available
        2. Considers patient's specific context and preferences  
        3. Optimizes for clinical outcomes, cost-effectiveness, and patient satisfaction
        4. Provides clear reasoning for each recommendation
        
        Return a structured pathway with steps, medications, monitoring, and reasoning.
        """
    
    async def _check_contraindications(self, context: PathwayContext) -> List[str]:
        """
        Dynamically check for contraindications based on user profile
        """
        contraindications = []
        
        # Use AI to analyze medical history for contraindications
        contra_analysis = await self.reasoning_engine.analyze_contraindications(
            condition=context.condition,
            medical_history=context.medical_history,
            current_medications=context.patient_profile.get("medications", []),
            allergies=context.patient_profile.get("allergies", [])
        )
        
        return contra_analysis.get("contraindications", [])


class SmartPathwayOrchestrator:
    """
    Orchestrates the intelligent pathway generation process
    """
    
    def __init__(self):
        self.dynamic_generator = DynamicPathwayGenerator()
        self.logger = logging.getLogger(__name__)
    
    async def generate_smart_pathway(
        self,
        condition: str,
        user_profile: Dict[str, Any],
        user_preferences: Dict[str, Any],
        regional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point for smart pathway generation
        """
        # Build context
        context = PathwayContext(
            condition=condition,
            patient_profile=user_profile,
            user_preferences=user_preferences,
            medical_history=user_profile.get("medical_history", []),
            regional_context=regional_context
        )
        
        # Generate intelligent pathway
        result = await self.dynamic_generator.generate_personalized_pathway(context)
        
        # Learn from this interaction for future improvements
        await self._learn_from_interaction(context, result)
        
        return result
    
    async def _learn_from_interaction(
        self,
        context: PathwayContext,
        result: Dict[str, Any]
    ):
        """
        Learn from user interactions to improve future recommendations
        """
        # Store interaction for machine learning
        interaction_data = {
            "condition": context.condition,
            "user_profile": context.patient_profile,
            "generated_pathway": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use this data to improve future recommendations
        await self.dynamic_generator.memory_store.store_interaction(interaction_data)
