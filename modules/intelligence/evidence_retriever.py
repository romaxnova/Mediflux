"""
Dynamic Evidence Retrieval System
Retrieves and synthesizes real-time medical evidence from multiple sources
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import re


@dataclass
class EvidenceSource:
    """Represents a medical evidence source"""
    name: str
    quality_score: float  # 0.0 to 1.0
    last_updated: datetime
    source_type: str  # "guideline", "research", "database", "registry"
    authority_level: str  # "international", "national", "regional", "local"


class EvidenceRetriever:
    """
    Dynamically retrieves medical evidence from multiple sources
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.evidence_cache = {}
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        
        # Medical authority sources with quality scoring
        self.sources = {
            "has_guidelines": EvidenceSource(
                name="HAS (Haute Autorité de Santé)",
                quality_score=0.95,
                last_updated=datetime.now(),
                source_type="guideline",
                authority_level="national"
            ),
            "esc_guidelines": EvidenceSource(
                name="European Society of Cardiology",
                quality_score=0.93,
                last_updated=datetime.now(),
                source_type="guideline", 
                authority_level="international"
            ),
            "cochrane_reviews": EvidenceSource(
                name="Cochrane Reviews",
                quality_score=0.98,
                last_updated=datetime.now(),
                source_type="research",
                authority_level="international"
            ),
            "bdpm_database": EvidenceSource(
                name="Base de Données Publique des Médicaments",
                quality_score=0.99,
                last_updated=datetime.now(),
                source_type="database",
                authority_level="national"
            )
        }
    
    async def get_has_guidelines(self, condition: str) -> Dict[str, Any]:
        """
        Retrieve HAS guidelines for a specific condition
        """
        cache_key = f"has_{condition}"
        if self._is_cached(cache_key):
            return self.evidence_cache[cache_key]
        
        try:
            # In a real implementation, this would query HAS APIs or databases
            # For now, we'll simulate intelligent evidence retrieval
            has_evidence = await self._simulate_has_query(condition)
            
            self.evidence_cache[cache_key] = {
                "source": self.sources["has_guidelines"],
                "evidence": has_evidence,
                "retrieved_at": datetime.now().isoformat()
            }
            
            return self.evidence_cache[cache_key]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve HAS guidelines for {condition}: {e}")
            return {"error": str(e), "source": "has_guidelines"}
    
    async def get_international_guidelines(self, condition: str) -> Dict[str, Any]:
        """
        Retrieve international medical guidelines
        """
        cache_key = f"international_{condition}"
        if self._is_cached(cache_key):
            return self.evidence_cache[cache_key]
        
        try:
            # Query multiple international sources
            international_evidence = await self._simulate_international_query(condition)
            
            self.evidence_cache[cache_key] = {
                "source": self.sources["esc_guidelines"],
                "evidence": international_evidence,
                "retrieved_at": datetime.now().isoformat()
            }
            
            return self.evidence_cache[cache_key]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve international guidelines for {condition}: {e}")
            return {"error": str(e), "source": "international_guidelines"}
    
    async def get_recent_research(self, condition: str) -> Dict[str, Any]:
        """
        Retrieve recent research and clinical studies
        """
        cache_key = f"research_{condition}"
        if self._is_cached(cache_key):
            return self.evidence_cache[cache_key]
        
        try:
            # In real implementation: PubMed API, Cochrane, clinical trials databases
            research_evidence = await self._simulate_research_query(condition)
            
            self.evidence_cache[cache_key] = {
                "source": self.sources["cochrane_reviews"],
                "evidence": research_evidence,
                "retrieved_at": datetime.now().isoformat()
            }
            
            return self.evidence_cache[cache_key]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve research for {condition}: {e}")
            return {"error": str(e), "source": "research"}
    
    async def get_medication_database(self, condition: str) -> Dict[str, Any]:
        """
        Retrieve medication data from BDPM and other pharmaceutical databases
        """
        cache_key = f"medications_{condition}"
        if self._is_cached(cache_key):
            return self.evidence_cache[cache_key]
        
        try:
            # Real implementation would query BDPM API, drug interaction databases
            medication_evidence = await self._simulate_medication_query(condition)
            
            self.evidence_cache[cache_key] = {
                "source": self.sources["bdpm_database"],
                "evidence": medication_evidence,
                "retrieved_at": datetime.now().isoformat()
            }
            
            return self.evidence_cache[cache_key]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve medication data for {condition}: {e}")
            return {"error": str(e), "source": "medication_database"}
    
    async def synthesize_evidence(
        self, 
        condition: str, 
        evidence_sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize evidence from multiple sources with quality weighting
        """
        try:
            valid_sources = [source for source in evidence_sources if "error" not in source]
            
            if not valid_sources:
                return {"error": "No valid evidence sources available"}
            
            # Weight evidence by source quality and recency
            weighted_evidence = self._weight_evidence_by_quality(valid_sources)
            
            # Generate overall confidence score
            confidence_score = self._calculate_confidence_score(weighted_evidence)
            
            # Extract key recommendations
            synthesized_recommendations = self._extract_key_recommendations(weighted_evidence)
            
            return {
                "condition": condition,
                "synthesized_evidence": weighted_evidence,
                "recommendations": synthesized_recommendations,
                "confidence_score": confidence_score,
                "evidence_quality": self._assess_evidence_quality(valid_sources),
                "synthesis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Evidence synthesis failed for {condition}: {e}")
            return {"error": f"Synthesis failed: {str(e)}"}
    
    async def get_regional_healthcare_data(
        self, 
        region: str, 
        providers_needed: List[str]
    ) -> Dict[str, Any]:
        """
        Get real-time regional healthcare data (wait times, availability, costs)
        """
        try:
            # In real implementation: query CNAMTS, ARS, hospital APIs
            regional_data = await self._simulate_regional_query(region, providers_needed)
            
            return {
                "region": region,
                "providers": providers_needed,
                "availability_data": regional_data,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve regional data for {region}: {e}")
            return {"error": str(e)}
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if evidence is cached and still valid"""
        if cache_key not in self.evidence_cache:
            return False
        
        cached_time = datetime.fromisoformat(
            self.evidence_cache[cache_key]["retrieved_at"]
        )
        
        return datetime.now() - cached_time < self.cache_duration
    
    def _weight_evidence_by_quality(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Weight evidence based on source quality and authority"""
        weighted_evidence = {}
        total_weight = 0
        
        for source_data in sources:
            if "source" in source_data and "evidence" in source_data:
                source = source_data["source"]
                evidence = source_data["evidence"]
                
                weight = source.quality_score
                total_weight += weight
                
                for key, value in evidence.items():
                    if key not in weighted_evidence:
                        weighted_evidence[key] = []
                    
                    weighted_evidence[key].append({
                        "value": value,
                        "weight": weight,
                        "source": source.name
                    })
        
        # Normalize weights
        for key in weighted_evidence:
            for item in weighted_evidence[key]:
                item["normalized_weight"] = item["weight"] / total_weight
        
        return weighted_evidence
    
    def _calculate_confidence_score(self, weighted_evidence: Dict[str, Any]) -> float:
        """Calculate overall confidence score based on evidence quality"""
        if not weighted_evidence:
            return 0.0
        
        # Calculate confidence based on evidence convergence and source quality
        total_confidence = 0
        evidence_count = 0
        
        for key, evidence_list in weighted_evidence.items():
            if evidence_list:
                # Higher confidence when multiple high-quality sources agree
                source_qualities = [item["weight"] for item in evidence_list]
                key_confidence = sum(source_qualities) / len(source_qualities)
                total_confidence += key_confidence
                evidence_count += 1
        
        return min(total_confidence / evidence_count if evidence_count > 0 else 0, 1.0)
    
    def _extract_key_recommendations(self, weighted_evidence: Dict[str, Any]) -> List[str]:
        """Extract key clinical recommendations from synthesized evidence"""
        recommendations = []
        
        # Extract recommendations based on highest weighted evidence
        for key, evidence_list in weighted_evidence.items():
            if evidence_list and "recommendation" in key.lower():
                # Get highest weighted recommendation
                best_evidence = max(evidence_list, key=lambda x: x["normalized_weight"])
                recommendations.append(best_evidence["value"])
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _assess_evidence_quality(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall quality of evidence sources"""
        if not sources:
            return {"overall_quality": 0.0, "grade": "D"}
        
        quality_scores = []
        source_types = set()
        
        for source_data in sources:
            if "source" in source_data:
                source = source_data["source"]
                quality_scores.append(source.quality_score)
                source_types.add(source.source_type)
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Grade evidence quality
        if avg_quality >= 0.9 and "guideline" in source_types:
            grade = "A"
        elif avg_quality >= 0.8:
            grade = "B"  
        elif avg_quality >= 0.6:
            grade = "C"
        else:
            grade = "D"
        
        return {
            "overall_quality": avg_quality,
            "grade": grade,
            "source_diversity": len(source_types),
            "guideline_based": "guideline" in source_types
        }
    
    # Simulation methods (in real implementation, these would be actual API calls)
    
    async def _simulate_has_query(self, condition: str) -> Dict[str, Any]:
        """Simulate HAS guideline query"""
        condition_lower = condition.lower()
        
        if "hypertension" in condition_lower or "hta" in condition_lower:
            return {
                "title": "Prise en charge de l'hypertension artérielle",
                "recommendations": [
                    "Mesures tensionnelles répétées pour confirmation diagnostique",
                    "Évaluation du risque cardiovasculaire global",
                    "Règles hygiéno-diététiques en première intention",
                    "Traitement pharmacologique si objectif non atteint"
                ],
                "evidence_level": "A",
                "target_values": {"systolic": "<140 mmHg", "diastolic": "<90 mmHg"},
                "first_line_treatments": ["IEC/ARA2", "Diurétiques thiazidiques", "Inhibiteurs calciques"]
            }
        
        elif "diabète" in condition_lower or "diabetes" in condition_lower:
            return {
                "title": "Stratégie médicamenteuse du contrôle glycémique du diabète de type 2",
                "recommendations": [
                    "Metformine en première intention",
                    "Objectif HbA1c <7% en général",
                    "Approche personnalisée selon profil patient",
                    "Prévention des complications cardiovasculaires"
                ],
                "evidence_level": "A",
                "target_values": {"hba1c": "<7%", "glycemie_jeun": "0.7-1.3 g/L"}
            }
        
        # Default for unknown conditions
        return {
            "title": f"Recommandations pour {condition}",
            "recommendations": ["Consultation médicale spécialisée recommandée"],
            "evidence_level": "C",
            "note": "Recommandations générales - consultation spécialisée requise"
        }
    
    async def _simulate_international_query(self, condition: str) -> Dict[str, Any]:
        """Simulate international guideline query"""
        # Similar structure but with international perspective
        return {
            "international_consensus": True,
            "contributing_societies": ["ESC", "AHA", "WHO"],
            "global_recommendations": ["Evidence-based approach", "Patient-centered care"],
            "regional_variations": {"europe": "ESC guidelines", "usa": "AHA guidelines"}
        }
    
    async def _simulate_research_query(self, condition: str) -> Dict[str, Any]:
        """Simulate recent research query"""
        return {
            "recent_studies": [
                {"title": f"Latest clinical trial for {condition}", "year": 2024, "evidence_level": "I"},
                {"title": f"Meta-analysis of {condition} treatments", "year": 2023, "evidence_level": "Ia"}
            ],
            "emerging_treatments": ["Novel therapeutic approaches under investigation"],
            "safety_updates": ["Recent safety alerts and contraindications"]
        }
    
    async def _simulate_medication_query(self, condition: str) -> Dict[str, Any]:
        """Simulate medication database query"""
        condition_lower = condition.lower()
        
        if "hypertension" in condition_lower:
            return {
                "first_line_medications": [
                    {"name": "Lisinopril", "class": "IEC", "cost": 8.20, "reimbursement": 0.65},
                    {"name": "Amlodipine", "class": "Inhibiteur calcique", "cost": 6.50, "reimbursement": 0.65}
                ],
                "contraindications": ["Grossesse", "Hyperkaliémie"],
                "interactions": ["AINS", "Suppléments potassium"]
            }
        
        return {"medications": "Database query required for specific condition"}
    
    async def _simulate_regional_query(self, region: str, providers: List[str]) -> Dict[str, Any]:
        """Simulate regional healthcare data query"""
        return {
            "wait_times": {
                "general_practitioner": "2-3 days",
                "cardiologist": "6-8 weeks",
                "endocrinologist": "4-6 weeks"
            },
            "availability": {
                "laboratories": "high",
                "imaging": "medium",
                "specialists": "variable"
            },
            "costs": {
                "consultation_gp": 25.0,
                "consultation_specialist": 50.0,
                "regional_modifier": 1.0
            }
        }
