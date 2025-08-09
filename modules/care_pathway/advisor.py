"""
Care Pathway Advisor for V2 Mediflux
Recommends optimized care sequences based on user profile and regional data
Integrates Annuaire Santé and Odissé data for intelligent routing
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
import sys
import os

# Add knowledge_base module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from knowledge_base.manager import KnowledgeBaseManager


class CarePathwayAdvisor:
    """
    Provides intelligent care pathway recommendations
    Optimizes for cost, wait times, and accessibility
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize knowledge base manager
        kb_path = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base')
        self.knowledge_base = KnowledgeBaseManager(kb_path)
        
        # Fallback pathway templates for conditions without structured knowledge
        self.pathway_templates = {
            "back_pain": [
                {"step": 1, "type": "gp_consultation", "urgency": "low"},
                {"step": 2, "type": "physiotherapy", "condition": "if_chronic"},
                {"step": 3, "type": "specialist_rheumatology", "condition": "if_severe"}
            ],
            "chest_pain": [
                {"step": 1, "type": "emergency_assessment", "urgency": "high"},
                {"step": 2, "type": "cardiology_consultation", "urgency": "medium"}
            ],
            "diabetes": [
                {"step": 1, "type": "gp_consultation", "urgency": "medium"},
                {"step": 2, "type": "endocrinology", "urgency": "medium"},
                {"step": 3, "type": "nutritionist", "urgency": "low"}
            ],
            "general": [
                {"step": 1, "type": "gp_consultation", "urgency": "low"}
            ]
        }
        
        # Cost estimates by care type (would be updated with real data)
        self.care_costs = {
            "gp_consultation": {"base": 25.00, "secteur_1": True},
            "specialist_consultation": {"base": 30.00, "secteur_1": True},
            "physiotherapy": {"base": 16.50, "secteur_1": True},
            "emergency_assessment": {"base": 0.00, "note": "Public hospital"},
            "imaging_mri": {"base": 250.00, "reimbursement": 0.70}
        }
    
    async def get_optimized_pathway(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get evidence-based optimized care pathway for a condition
        
        Args:
            params: Dictionary containing condition, location, user_profile
            
        Returns:
            Structured pathway with evidence sources and confidence scores
        """
        try:
            condition = params.get("condition", "").lower()
            location = params.get("location", "paris").lower()
            user_profile = params.get("user_profile", {})
            
            # Try to get structured knowledge first
            pathway_data = self.knowledge_base.get_clinical_pathway(
                condition=condition,
                severity="standard",
                region=location
            )
            
            if pathway_data.get("pathway"):
                # Use knowledge base pathway
                return await self._format_knowledge_based_pathway(pathway_data, params)
            else:
                # Fallback to template-based pathway
                return await self._get_template_based_pathway(condition, params)
                
        except Exception as e:
            self.logger.error(f"Pathway generation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate pathway: {str(e)}"
            }
    
    async def _format_knowledge_based_pathway(self, pathway_data: Dict, params: Dict) -> Dict:
        """
        Format knowledge base pathway data for orchestrator response
        """
        condition = pathway_data["condition"]
        pathway = pathway_data["pathway"]
        location = params.get("location", "paris")
        
        # Convert pathway steps to structured format
        pathway_steps = []
        total_cost = 0
        
        for step_key, step_data in pathway.items():
            if isinstance(step_data, dict) and "action" in step_data:
                step_number = int(step_key.split("_")[-1]) if "_" in step_key else len(pathway_steps) + 1
                
                step_cost = step_data.get("cost_estimate", {})
                step_total = sum(step_cost.values()) if isinstance(step_cost, dict) else 0
                total_cost += step_total
                
                pathway_steps.append({
                    "step": step_number,
                    "type": step_data["action"],
                    "timing": step_data.get("timing", "standard"),
                    "rationale": step_data.get("rationale", ""),
                    "cost": step_total,
                    "wait_time": step_data.get("wait_time", "standard")
                })
        
        # Get medication options
        medications = self.knowledge_base.get_medication_options(
            condition, params.get("user_profile", {})
        )
        
        # Get quality indicators
        quality_metrics = self.knowledge_base.get_quality_indicators(condition)
        
        return {
            "success": True,
            "condition": condition,
            "pathway_steps": pathway_steps,
            "cost_breakdown": {
                "total_estimated_cost": total_cost,
                "patient_cost": total_cost * 0.30,  # Rough estimate, would be calculated precisely
                "evidence_based": True
            },
            "medications": medications[:3],  # Top 3 medication options
            "regional_context": {
                "location": location,
                "data_source": "knowledge_base",
                "last_updated": pathway_data.get("last_updated")
            },
            "quality_indicators": quality_metrics,
            "evidence": {
                "level": pathway_data.get("evidence_level", "C"),
                "source": pathway_data.get("source", "Clinical guidelines"),
                "confidence": pathway_data.get("confidence", 0.7)
            },
            "optimization_tips": [
                f"Pathway based on {pathway_data.get('source', 'clinical evidence')}",
                f"Success rate: {quality_metrics.get('success_rate', 'N/A')}",
                f"Average resolution: {quality_metrics.get('resolution_time_days', 'N/A')} days"
            ]
        }
    
    async def _get_template_based_pathway(self, condition: str, params: Dict) -> Dict:
        """
        Fallback to template-based pathway when knowledge base doesn't have data
        """
        user_location = params.get("location", "Paris")
        preferences = params.get("preferences", {})
        
        # Get base pathway template
        pathway_template = self._get_pathway_template(condition)
        
        # Customize pathway based on user preferences and location
        optimized_pathway = await self._optimize_pathway(
            pathway_template, 
            user_location, 
            preferences
        )
        
        # Add cost estimates
        cost_breakdown = await self._calculate_pathway_costs(optimized_pathway, params)
        
        # Add regional context
        regional_info = await self._get_regional_context(user_location, condition)
        
        return {
            "success": True,
            "condition": condition,
            "pathway_steps": optimized_pathway,
            "cost_breakdown": cost_breakdown,
            "regional_context": regional_info,
            "estimated_timeline": self._calculate_timeline(optimized_pathway),
            "optimization_tips": self._generate_optimization_tips(optimized_pathway, preferences),
            "evidence": {
                "level": "Template",
                "source": "Standard protocols",
                "confidence": 0.6
            }
        }
    
    async def get_optimized_pathway_legacy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get optimized care pathway recommendation
        
        Args:
            params: Dictionary containing:
                - condition: Medical condition or symptoms
                - user_location: User's location
                - preferences: Cost/time preferences
                - pathology: Existing conditions
                
        Returns:
            Recommended care pathway with cost estimates
        """
        try:
            condition = params.get("condition", "general").lower()
            user_location = params.get("user_location", "Paris")
            preferences = params.get("preferences", {})
            
            # Get base pathway template
            pathway_template = self._get_pathway_template(condition)
            
            # Customize pathway based on user preferences and location
            optimized_pathway = await self._optimize_pathway(
                pathway_template, 
                user_location, 
                preferences
            )
            
            # Add cost estimates
            cost_breakdown = await self._calculate_pathway_costs(optimized_pathway, params)
            
            # Add regional context
            regional_info = await self._get_regional_context(user_location, condition)
            
            return {
                "success": True,
                "condition": condition,
                "pathway_steps": optimized_pathway,
                "cost_breakdown": cost_breakdown,
                "regional_context": regional_info,
                "estimated_timeline": self._estimate_timeline(optimized_pathway),
                "optimization_tips": self._generate_optimization_tips(optimized_pathway, preferences)
            }
            
        except Exception as e:
            self.logger.error(f"Pathway optimization failed: {str(e)}")
            return {
                "success": False,
                "error": f"Pathway optimization failed: {str(e)}"
            }
    
    def _get_pathway_template(self, condition: str) -> List[Dict[str, Any]]:
        """
        Get appropriate pathway template for condition
        """
        # Map condition keywords to templates
        condition_mappings = {
            "dos": "back_pain",
            "mal de dos": "back_pain",
            "lombalgie": "back_pain",
            "douleur thoracique": "chest_pain",
            "chest pain": "chest_pain",
            "diabète": "diabetes",
            "diabetes": "diabetes"
        }
        
        # Find matching template
        for keyword, template_key in condition_mappings.items():
            if keyword in condition.lower():
                return self.pathway_templates[template_key].copy()
        
        # Default to general pathway
        return self.pathway_templates["general"].copy()
    
    async def _optimize_pathway(self, pathway: List[Dict[str, Any]], location: str, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Optimize pathway based on location and preferences
        """
        optimized = []
        
        for step in pathway:
            optimized_step = step.copy()
            
            # Add location-specific recommendations
            if step["type"] == "gp_consultation":
                optimized_step["location_advice"] = f"Secteur 1 GPs available in {location}"
                optimized_step["estimated_wait"] = "2-3 days"
            
            elif step["type"] == "specialist_consultation":
                optimized_step["location_advice"] = f"Consider public hospital specialists in {location}"
                optimized_step["estimated_wait"] = "2-4 weeks"
            
            # Apply cost preferences
            cost_preference = preferences.get("cost_priority", "balanced")
            if cost_preference == "low_cost":
                optimized_step["sector_preference"] = "secteur_1"
                optimized_step["facility_preference"] = "public"
            
            optimized.append(optimized_step)
        
        return optimized
    
    async def _calculate_pathway_costs(self, pathway: List[Dict[str, Any]], user_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate total costs for the pathway
        """
        total_cost = 0
        step_costs = []
        mutuelle_type = user_params.get("user_mutuelle", "basic")
        
        for step in pathway:
            care_type = step["type"]
            
            if care_type in self.care_costs:
                cost_info = self.care_costs[care_type]
                base_cost = cost_info["base"]
                
                # Apply reimbursement calculation (simplified)
                secu_coverage = base_cost * 0.70  # 70% standard rate
                mutuelle_coverage = (base_cost - secu_coverage) * (0.30 if mutuelle_type == "basic" else 0.50)
                patient_cost = base_cost - secu_coverage - mutuelle_coverage
                
                step_cost = {
                    "step": step.get("step", 0),
                    "type": care_type,
                    "base_cost": base_cost,
                    "patient_cost": max(0, round(patient_cost, 2))
                }
                
                step_costs.append(step_cost)
                total_cost += step_cost["patient_cost"]
        
        return {
            "total_patient_cost": round(total_cost, 2),
            "step_by_step_costs": step_costs,
            "estimated_total_with_coverage": round(sum(s["base_cost"] for s in step_costs), 2)
        }
    
    async def _get_regional_context(self, location: str, condition: str) -> Dict[str, Any]:
        """
        Get regional healthcare context
        TODO: Integrate with Odissé API for real data
        """
        # Placeholder regional data
        return {
            "location": location,
            "specialist_density": "medium",
            "average_wait_times": {
                "gp": "2-3 days",
                "specialist": "2-4 weeks"
            },
            "public_hospital_access": "good",
            "transport_accessibility": "good",
            "data_source": "estimated"  # Would be "odisse" with real integration
        }
    
    def _estimate_timeline(self, pathway: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Estimate timeline for pathway completion
        """
        total_weeks = 0
        timeline_steps = []
        
        for step in pathway:
            # Estimate wait times based on care type
            care_type = step["type"]
            
            if care_type == "gp_consultation":
                wait_weeks = 0.5  # Few days
            elif "specialist" in care_type:
                wait_weeks = 3  # 3 weeks average
            elif care_type == "physiotherapy":
                wait_weeks = 1  # 1 week
            else:
                wait_weeks = 1  # Default
            
            total_weeks += wait_weeks
            
            timeline_steps.append({
                "step": step.get("step", 0),
                "weeks_from_start": total_weeks,
                "type": care_type
            })
        
        return {
            "total_estimated_weeks": total_weeks,
            "timeline_breakdown": timeline_steps,
            "urgency_note": "Timeline may be shorter for urgent conditions"
        }
    
    def _generate_optimization_tips(self, pathway: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[str]:
        """
        Generate tips for optimizing the care pathway
        """
        tips = []
        
        # General tips
        tips.append("Start with your GP to ensure proper care coordination")
        
        # Cost optimization tips
        cost_preference = preferences.get("cost_priority", "balanced")
        if cost_preference == "low_cost":
            tips.extend([
                "Choose Secteur 1 practitioners to minimize out-of-pocket costs",
                "Consider public hospital specialists for specialized care",
                "Use your carte vitale for direct reimbursement"
            ])
        
        # Time optimization tips
        if preferences.get("time_priority") == "fast":
            tips.extend([
                "Consider private practitioners for faster appointments",
                "Check if teleconsultation is available for follow-ups"
            ])
        
        # Pathway-specific tips
        if len(pathway) > 2:
            tips.append("This pathway may take several weeks - plan accordingly")
        
        return tips
    
    async def get_pathway_context(self, specialty: str, pathology: str) -> Dict[str, Any]:
        """
        Get additional context for a specific specialty and pathology combination
        """
        return {
            "specialty": specialty,
            "pathology": pathology,
            "typical_pathway": f"For {pathology}, {specialty} consultations typically follow GP assessment",
            "cost_range": "€25-60 per consultation",
            "wait_time_estimate": "2-4 weeks for specialist appointment"
        }
