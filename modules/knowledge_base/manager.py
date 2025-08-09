"""
Knowledge Base Manager for Mediflux V2
Provides structured, evidence-based medical knowledge for pathway recommendations
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime


class KnowledgeBaseManager:
    """
    Manages structured medical knowledge for evidence-based recommendations
    Integrates clinical guidelines, regional data, and real-time costs
    """
    
    def __init__(self, kb_path: str = "knowledge_base"):
        self.kb_path = Path(kb_path)
        self.logger = logging.getLogger(__name__)
        self._pathology_cache = {}
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load all pathology knowledge files into memory"""
        pathologies_dir = self.kb_path / "pathologies"
        
        if not pathologies_dir.exists():
            self.logger.warning(f"Knowledge base directory not found: {pathologies_dir}")
            return
            
        for json_file in pathologies_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    pathology_data = json.load(f)
                    
                pathology_name = json_file.stem
                self._pathology_cache[pathology_name] = pathology_data
                
                # Also index by aliases
                aliases = pathology_data.get("pathology", {}).get("aliases", [])
                for alias in aliases:
                    self._pathology_cache[alias.lower()] = pathology_data
                    
            except Exception as e:
                self.logger.error(f"Failed to load {json_file}: {e}")
    
    def get_pathology_info(self, condition: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive pathology information
        
        Args:
            condition: Pathology name or alias
            
        Returns:
            Complete pathology data or None if not found
        """
        condition_normalized = condition.lower().replace(" ", "_")
        
        # Try exact match first
        if condition_normalized in self._pathology_cache:
            return self._pathology_cache[condition_normalized]
        
        # Try partial matching
        for key, data in self._pathology_cache.items():
            if condition_normalized in key or key in condition_normalized:
                return data
                
        return None
    
    def get_clinical_pathway(self, condition: str, severity: str = "standard", 
                           region: str = "paris") -> Dict[str, Any]:
        """
        Get evidence-based clinical pathway for a condition
        
        Args:
            condition: Medical condition
            severity: simple/compliquée/récidivante
            region: Geographic region for local data
            
        Returns:
            Structured pathway with steps, costs, and evidence
        """
        pathology_data = self.get_pathology_info(condition)
        
        if not pathology_data:
            return self._get_default_pathway(condition)
        
        clinical_pathway = pathology_data.get("clinical_pathway", {})
        regional_data = pathology_data.get("regional_data", {}).get(region.lower(), {})
        
        # Select appropriate protocol
        if severity == "emergency":
            protocol = clinical_pathway.get("emergency_protocol", {})
        else:
            protocol = clinical_pathway.get("standard_protocol", {})
        
        # Enrich with regional and cost data
        enriched_pathway = self._enrich_pathway_with_regional_data(
            protocol, regional_data, pathology_data
        )
        
        return {
            "condition": condition,
            "pathway": enriched_pathway,
            "evidence_level": clinical_pathway.get("evidence_level", "C"),
            "source": clinical_pathway.get("source", "Clinical guidelines"),
            "confidence": pathology_data.get("confidence_score", {}).get("overall", 0.7),
            "last_updated": clinical_pathway.get("last_updated"),
            "region": region
        }
    
    def get_medication_options(self, condition: str, patient_profile: Dict = None) -> List[Dict]:
        """
        Get medication recommendations for a condition
        
        Args:
            condition: Medical condition
            patient_profile: Patient contraindications, allergies, etc.
            
        Returns:
            List of medication options with costs and rationale
        """
        pathology_data = self.get_pathology_info(condition)
        
        if not pathology_data:
            return []
        
        medications = pathology_data.get("medications", {})
        first_line = medications.get("first_line", [])
        
        # Filter based on patient profile
        if patient_profile:
            first_line = self._filter_medications_by_profile(first_line, patient_profile, pathology_data)
        
        return first_line
    
    def get_quality_indicators(self, condition: str) -> Dict[str, Any]:
        """
        Get quality and effectiveness indicators for a condition
        
        Args:
            condition: Medical condition
            
        Returns:
            Quality metrics including success rates, satisfaction, etc.
        """
        pathology_data = self.get_pathology_info(condition)
        
        if not pathology_data:
            return {}
        
        return pathology_data.get("quality_indicators", {})
    
    def _enrich_pathway_with_regional_data(self, protocol: Dict, regional_data: Dict, 
                                         pathology_data: Dict) -> Dict[str, Any]:
        """Enrich pathway steps with regional costs and availability"""
        enriched_steps = {}
        
        for step_key, step_data in protocol.items():
            if isinstance(step_data, dict):
                enriched_step = step_data.copy()
                
                # Add regional wait times
                if "consultation" in step_data.get("action", "").lower():
                    enriched_step["wait_time"] = regional_data.get("gp_availability", "2-3 jours")
                
                # Update costs with regional data
                if "cost_estimate" in step_data:
                    regional_costs = regional_data.get("average_cost", {})
                    for cost_type, amount in regional_costs.items():
                        if cost_type in enriched_step.get("cost_estimate", {}):
                            enriched_step["cost_estimate"][cost_type] = amount
                
                enriched_steps[step_key] = enriched_step
            else:
                enriched_steps[step_key] = step_data
        
        return enriched_steps
    
    def _filter_medications_by_profile(self, medications: List[Dict], 
                                     patient_profile: Dict, pathology_data: Dict) -> List[Dict]:
        """Filter medications based on patient contraindications"""
        filtered_meds = []
        contraindications = pathology_data.get("contraindications", {})
        
        for med in medications:
            is_safe = True
            
            # Check pregnancy
            if patient_profile.get("pregnant"):
                pregnancy_avoid = contraindications.get("pregnancy", {}).get("avoid", [])
                if med["name"] in pregnancy_avoid:
                    is_safe = False
            
            # Check renal function
            if patient_profile.get("renal_insufficiency"):
                renal_avoid = contraindications.get("renal_insufficiency", {}).get("avoid", [])
                if med["name"] in renal_avoid:
                    is_safe = False
            
            if is_safe:
                filtered_meds.append(med)
        
        return filtered_meds
    
    def _get_default_pathway(self, condition: str) -> Dict[str, Any]:
        """Return a generic pathway when specific knowledge is not available"""
        return {
            "condition": condition,
            "pathway": {
                "step_1": {
                    "action": "Consultation médecin généraliste",
                    "timing": "2-3 jours",
                    "rationale": "Évaluation initiale et diagnostic",
                    "cost_estimate": {"consultation": 25.00}
                }
            },
            "evidence_level": "Generic",
            "source": "Default protocol",
            "confidence": 0.5,
            "region": "general"
        }
    
    def update_quality_indicators(self, condition: str, feedback: Dict[str, Any]):
        """
        Update quality indicators based on user feedback
        
        Args:
            condition: Medical condition
            feedback: User feedback data (success, satisfaction, etc.)
        """
        # This would update the knowledge base with real user feedback
        # For MVP, we can log this for future analysis
        self.logger.info(f"Feedback received for {condition}: {feedback}")
    
    def get_knowledge_confidence(self, condition: str) -> float:
        """
        Get confidence score for knowledge about a specific condition
        
        Args:
            condition: Medical condition
            
        Returns:
            Confidence score between 0 and 1
        """
        pathology_data = self.get_pathology_info(condition)
        
        if not pathology_data:
            return 0.3  # Low confidence for unknown conditions
        
        return pathology_data.get("confidence_score", {}).get("overall", 0.7)
    
    def list_supported_conditions(self) -> List[str]:
        """Get list of conditions with structured knowledge"""
        conditions = []
        for key, data in self._pathology_cache.items():
            if isinstance(data, dict) and "pathology" in data:
                conditions.append(data["pathology"]["name"])
        
        return list(set(conditions))  # Remove duplicates
