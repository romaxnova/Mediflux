"""
Intent Router for V2 Mediflux
Rule-based intent matching with fallback to local AI
Lightweight and fast for common queries
"""

import re
import json
from typing import Dict, List, Any, Optional
import asyncio


class IntentRouter:
    """
    Routes user queries to appropriate intents using rule-based matching
    Falls back to local AI (Mixtral) for complex/ambiguous queries
    """
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_extractors = self._load_entity_extractors()
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Load rule-based patterns for intent matching
        """
        return {
            "simulate_cost": [
                r"combien.*(coûte|coute|prix|remboursement)",
                r"(prix|cost|tarif).*médicament",
                r"remboursement.*mutuelle",
                r"reste à charge",
                r"simulation.*coût",
                r"calculate.*cost"
            ],
            "analyze_document": [
                r"(analyser|analyse|upload|télécharger).*document",
                r"carte.*tiers.*payant",
                r"feuille.*soins",
                r"parse.*document",
                r"extract.*information"
            ],
            "care_pathway": [
                r"parcours.*soins",
                r"chemin.*médical", 
                r"itinéraire.*santé",
                r"care.*pathway",
                r"séquence.*consultation",
                r"où.*consulter",
                r"recommandation.*spécialiste",
                # Enhanced patterns for better detection
                r"meilleur.*parcours",
                r"parcours.*optimal",
                r"comment.*traiter",
                r"traitement.*pour",
                r"soins.*pour",
                r"suivi.*médical",
                r"protocole.*soins",
                r"prise.*en.*charge",
                r"étapes.*traitement",
                r"démarche.*médicale",
                r"gestion.*maladie",
                r"stratégie.*thérapeutique"
            ],
            "medication_info": [
                r"médicament.*\b\w+",
                r"information.*médicament", 
                r"doliprane|aspirin|paracétamol|ibuprofène",
                r"substance.*active",
                r"medication.*information",
                r"drug.*information",
                # Enhanced patterns for sleep aids and OTC medications
                r"somnifère|somnifere|sleeping.*pill",
                r"trouve.*moi.*(médicament|somnifère|anti.*douleur)",
                r"sans.*ordonnance",
                r"médicament.*libre",
                r"over.*the.*counter",
                r"automédication"
            ],
            "practitioner_search": [
                r"trouver.*(médecin|docteur|spécialiste)",
                r"chercher.*(praticien|cabinet)",
                r"find.*(doctor|practitioner)",
                r"cardiologue|dentiste|kinésithérapeute|sage-femme",
                r"hôpital|clinique|centre.*médical",
                # Enhanced patterns for finding healthcare providers
                r"où.*consulter",
                r"besoin.*d.*un.*(médecin|docteur)",
                r"consultation.*avec.*(spécialiste|généraliste)"
            ]
        }
    
    def _load_entity_extractors(self) -> Dict[str, List[str]]:
        """
        Load patterns for extracting entities from queries
        """
        return {
            "location": [
                r"à\s+([A-Za-z\s-]+)(?:\s|$)",
                r"dans\s+([A-Za-z\s-]+)(?:\s|$)",
                r"(\d{5})",  # Postal codes
                r"([1-2]?\d[er]+\s*arrondissement)",  # Paris arrondissements
                r"in\s+([A-Za-z\s-]+)(?:\s|$)"
            ],
            "medication_name": [
                r"(?:médicament|medication|drug)\s+([A-Za-z0-9\s-]+)",
                r"(doliprane|aspirin|paracétamol|ibuprofène|amoxicilline)",
                r"([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s*(?:mg|g|ml|comprimé|gélule)"
            ],
            "specialty": [
                r"(cardiologue|cardiologist)",
                r"(dentiste|dentist)",
                r"(kinésithérapeute|physiotherapist)",
                r"(sage-femme|midwife)",
                r"(ophtalmologue|ophthalmologist)",
                r"(dermatologue|dermatologist)",
                r"(gynécologue|gynecologist)"
            ],
            "location": [
                r"(?:à|in|dans|en|sur)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(?:ville|city)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"(paris|lyon|marseille|toulouse|nice|nantes|strasbourg|montpellier|bordeaux|lille|rennes|reims|le havre|saint-étienne|toulon|grenoble|dijon|angers|nîmes|villeurbanne)"
            ],
            "document_type": [
                r"carte.*tiers.*payant",
                r"feuille.*soins",
                r"ordonnance",
                r"prescription",
                r"insurance.*card"
            ]
        }
    
    async def route_intent(self, user_query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main routing function - determines intent and extracts parameters
        
        Args:
            user_query: User's natural language query
            user_context: User's stored context/profile
            
        Returns:
            Dict with intent, confidence, and extracted parameters
        """
        query_lower = user_query.lower()
        
        # Step 1: Rule-based intent matching
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = self._calculate_pattern_score(query_lower, patterns)
            if score > 0:
                intent_scores[intent] = score
        
        # Step 2: Determine best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent] * 0.1, 1.0)  # Scale to 0-1
        else:
            # Fallback to AI interpretation for complex queries
            return await self._ai_fallback_interpretation(user_query, user_context)
        
        # Step 3: Extract entities based on intent
        extracted_params = self._extract_entities_for_intent(user_query, best_intent)
        
        # Step 4: Enrich with context if available
        if user_context:
            extracted_params = self._enrich_with_context(extracted_params, user_context)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "params": extracted_params,
            "method": "rule_based"
        }
    
    def _calculate_pattern_score(self, query: str, patterns: List[str]) -> float:
        """
        Calculate matching score for a set of patterns
        """
        total_score = 0
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Higher score for more specific/longer patterns
                pattern_specificity = len(pattern) / 20.0  # Normalize
                total_score += 1 + pattern_specificity
        return total_score
    
    def _extract_entities_for_intent(self, query: str, intent: str) -> Dict[str, Any]:
        """
        Extract relevant entities based on the detected intent
        """
        params = {}
        
        # Always try to extract location
        location = self._extract_entity(query, "location")
        if location:
            params["location"] = location
        
        if intent == "simulate_cost":
            medication = self._extract_entity(query, "medication_name")
            if medication:
                params["medication_name"] = medication
            
            # Look for price mentions
            price_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:€|euros?)", query, re.IGNORECASE)
            if price_match:
                params["mentioned_price"] = price_match.group(1)
        
        elif intent == "medication_info":
            medication = self._extract_entity(query, "medication_name")
            if medication:
                params["medication_name"] = medication
            
            # Determine search type
            if re.search(r"substance.*active", query, re.IGNORECASE):
                params["search_type"] = "substance"
            elif re.search(r"CIS\s*\d+", query, re.IGNORECASE):
                params["search_type"] = "cis_code"
                cis_match = re.search(r"CIS\s*(\d+)", query, re.IGNORECASE)
                if cis_match:
                    params["cis_code"] = cis_match.group(1)
            else:
                params["search_type"] = "name"
        
        elif intent == "practitioner_search":
            specialty = self._extract_entity(query, "specialty")
            if specialty:
                params["specialty"] = specialty
            
            location = self._extract_entity(query, "location")
            if location:
                params["location"] = location
            
            # Extract practitioner name if mentioned
            name_patterns = [
                r"(?:docteur|dr\.?|médecin)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:médecin|docteur)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    params["practitioner_name"] = match.group(1)
                    break
        
        elif intent == "analyze_document":
            doc_type = self._extract_entity(query, "document_type")
            if doc_type:
                params["document_type"] = doc_type
            else:
                params["document_type"] = "auto_detect"
        
        elif intent == "care_pathway":
            # Extract condition/pathology mentions
            condition_patterns = [
                r"pour.*ma\s*([A-Za-z\s-]+)",
                r"avec.*(?:mon|ma)\s*([A-Za-z\s-]+)",
                r"(?:maladie|condition|pathologie)\s*([A-Za-z\s-]+)"
            ]
            for pattern in condition_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    params["condition"] = match.group(1).strip()
                    break
        
        return params
    
    def _extract_entity(self, query: str, entity_type: str) -> Optional[str]:
        """
        Extract a specific type of entity from the query
        """
        if entity_type not in self.entity_extractors:
            return None
        
        patterns = self.entity_extractors[entity_type]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Return the first capturing group, or the full match if no groups
                return match.group(1) if match.groups() else match.group(0)
        
        return None
    
    def _enrich_with_context(self, params: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich extracted parameters with user context
        """
        enriched_params = params.copy()
        
        user_profile = user_context.get("profile", {})
        
        # Add default location if not specified
        if "location" not in enriched_params and "location" in user_profile:
            enriched_params["default_location"] = user_profile["location"]
        
        # Add pathology context
        if "pathology" in user_profile:
            enriched_params["user_pathology"] = user_profile["pathology"]
        
        # Add mutuelle context
        if "mutuelle" in user_profile:
            enriched_params["user_mutuelle"] = user_profile["mutuelle"]
        
        return enriched_params
    
    async def _ai_fallback_interpretation(self, user_query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fallback to local AI (Mixtral) for complex query interpretation
        TODO: Implement when local Mixtral is set up
        """
        # For now, return a general intent with low confidence
        # This would be replaced with actual Mixtral API call
        return {
            "intent": "general_query",
            "confidence": 0.3,
            "params": {"original_query": user_query},
            "method": "ai_fallback",
            "note": "Complex query detected - AI interpretation not yet implemented"
        }
    
    def add_custom_pattern(self, intent: str, pattern: str) -> None:
        """
        Allow dynamic addition of custom patterns
        """
        if intent not in self.intent_patterns:
            self.intent_patterns[intent] = []
        self.intent_patterns[intent].append(pattern)
    
    def get_supported_intents(self) -> List[str]:
        """
        Return list of supported intents
        """
        return list(self.intent_patterns.keys())
