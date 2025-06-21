"""
Phase 2: Smart Context & Alternatives Engine
Provides intelligent suggestions when no matches are found.
"""

import difflib
from typing import Dict, List, Any, Optional, Tuple
import re


class SuggestionEngine:
    """Engine for generating smart alternatives when queries return no results"""
    
    def __init__(self):
        # Common specialty variations and alternatives
        self.specialty_alternatives = {
            "cardiologue": ["interniste", "médecin généraliste", "pneumologue"],
            "dermatologue": ["allergologue", "médecin généraliste", "rhumatologue"],
            "gynécologue": ["sage-femme", "urologue", "médecin généraliste"],
            "pédiatre": ["médecin généraliste", "allergologue", "psychiatre"],
            "psychiatre": ["psychologue", "médecin généraliste", "neurologue"],
            "dentiste": ["stomatologue", "chirurgien maxillo-facial", "orthodontiste"],
            "ophtalmologiste": ["médecin généraliste", "neurologue", "oto-rhino-laryngologiste"],
            "sage-femme": ["gynécologue", "médecin généraliste", "pédiatre"],
            "kinésithérapeute": ["ostéopathe", "rhumatologue", "médecin du sport"],
            "pharmacien": ["médecin généraliste", "toxicologue", "biologiste"],
        }
        
        # Paris arrondissement neighbors for geographic alternatives  
        self.arrond_neighbors = {
            "75001": ["75002", "75004", "75008", "75009"],
            "75002": ["75001", "75003", "75009", "75010"],
            "75003": ["75002", "75004", "75010", "75011"],
            "75004": ["75001", "75003", "75005", "75011", "75012"],
            "75005": ["75004", "75006", "75012", "75013"],
            "75006": ["75005", "75007", "75014", "75015"],
            "75007": ["75006", "75008", "75015", "75016"],
            "75008": ["75001", "75007", "75009", "75016", "75017"],
            "75009": ["75001", "75002", "75008", "75010", "75017", "75018"],
            "75010": ["75002", "75003", "75009", "75011", "75018", "75019"],
            "75011": ["75003", "75004", "75010", "75012", "75019", "75020"],
            "75012": ["75004", "75005", "75011", "75013", "75020"],
            "75013": ["75005", "75012", "75014"],
            "75014": ["75006", "75013", "75015"],
            "75015": ["75006", "75007", "75014", "75016"],
            "75016": ["75007", "75008", "75015", "75017"],
            "75017": ["75008", "75009", "75016", "75018"],
            "75018": ["75009", "75010", "75017", "75019"],
            "75019": ["75010", "75011", "75018", "75020"],
            "75020": ["75011", "75012", "75019"],
        }
        
        # Common query intent patterns
        self.intent_patterns = {
            "urgent": ["urgence", "urgent", "emergency", "maintenant", "aujourd'hui"],
            "consultation": ["consultation", "rendez-vous", "appointment", "voir"],
            "specialist": ["spécialiste", "specialist", "expert"],
            "nearby": ["près", "proche", "near", "autour", "around"]
        }

    def generate_alternatives(self, 
                            original_query: str, 
                            parsed_params: Dict[str, Any], 
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate smart alternatives when no results are found
        
        Args:
            original_query: The original user query
            parsed_params: Extracted parameters (specialty, postal_code, etc.)
            context: Additional context information
            
        Returns:
            Dictionary with suggestions and alternative parameters
        """
        suggestions = {
            "specialty_alternatives": [],
            "location_alternatives": [],
            "broader_search": {},
            "tips": [],
            "alternative_queries": []
        }
        
        # Extract query intent
        intent = self._analyze_intent(original_query)
        
        # Generate specialty alternatives
        if parsed_params.get("specialty"):
            specialty_suggestions = self._get_specialty_alternatives(
                parsed_params["specialty"], intent
            )
            suggestions["specialty_alternatives"] = specialty_suggestions
            
        # Generate location alternatives
        if parsed_params.get("address_postalcode"):
            location_suggestions = self._get_location_alternatives(
                parsed_params["address_postalcode"]
            )
            suggestions["location_alternatives"] = location_suggestions
            
        # Generate broader search parameters
        suggestions["broader_search"] = self._get_broader_search_params(parsed_params)
        
        # Generate contextual tips
        suggestions["tips"] = self._generate_tips(original_query, parsed_params, intent)
        
        # Generate alternative query suggestions
        suggestions["alternative_queries"] = self._generate_alternative_queries(
            original_query, parsed_params, intent
        )
        
        return suggestions

    def _analyze_intent(self, query: str) -> Dict[str, bool]:
        """Analyze user intent from query text"""
        intent = {}
        query_lower = query.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            intent[intent_type] = any(pattern in query_lower for pattern in patterns)
            
        return intent

    def _get_specialty_alternatives(self, specialty: str, intent: Dict[str, bool]) -> List[Dict[str, str]]:
        """Get alternative specialties based on the requested one"""
        alternatives = []
        
        # Direct alternatives from our mapping
        if specialty in self.specialty_alternatives:
            for alt_specialty in self.specialty_alternatives[specialty]:
                alternatives.append({
                    "specialty": alt_specialty,
                    "reason": "Specialité similaire",
                    "priority": "high"
                })
        
        # Fuzzy matching for similar specialties
        all_specialties = list(self.specialty_alternatives.keys())
        similar = difflib.get_close_matches(specialty, all_specialties, n=3, cutoff=0.6)
        
        for similar_specialty in similar:
            if similar_specialty != specialty:
                alternatives.append({
                    "specialty": similar_specialty,
                    "reason": "Spécialité proche",
                    "priority": "medium"
                })
        
        # If urgent, prioritize general practitioners
        if intent.get("urgent"):
            alternatives.insert(0, {
                "specialty": "médecin généraliste",
                "reason": "Disponible plus rapidement pour les urgences",
                "priority": "urgent"
            })
            
        return alternatives[:5]  # Limit to top 5 suggestions

    def _get_location_alternatives(self, postal_code: str) -> List[Dict[str, str]]:
        """Get alternative locations (nearby arrondissements)"""
        alternatives = []
        
        if postal_code in self.arrond_neighbors:
            neighbors = self.arrond_neighbors[postal_code]
            for neighbor in neighbors[:3]:  # Top 3 neighbors
                arrond_num = neighbor[-2:]
                alternatives.append({
                    "postal_code": neighbor,
                    "location": f"Paris {arrond_num}e arrondissement",
                    "reason": "Arrondissement adjacent",
                    "priority": "high"
                })
        
        # Add broader Paris suggestion
        if postal_code.startswith("75"):
            alternatives.append({
                "postal_code": "75*",
                "location": "Tout Paris",
                "reason": "Recherche élargie à Paris",
                "priority": "medium"
            })
            
        return alternatives

    def _get_broader_search_params(self, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameters for a broader search"""
        broader_params = original_params.copy()
        
        # Remove most restrictive filters
        if "specialty" in broader_params and "address_postalcode" in broader_params:
            # Keep location, remove specialty restriction
            return {"address_postalcode": broader_params["address_postalcode"]}
        elif "specialty" in broader_params:
            # Remove specialty, search all healthcare providers
            return {}
        elif "address_postalcode" in broader_params:
            # Keep specialty, expand location
            result = {k: v for k, v in broader_params.items() if k != "address_postalcode"}
            return result
            
        return {}

    def _generate_tips(self, query: str, params: Dict[str, Any], intent: Dict[str, bool]) -> List[str]:
        """Generate helpful tips based on the query"""
        tips = []
        
        if intent.get("urgent"):
            tips.append("💡 Pour les urgences, contactez le 15 (SAMU) ou rendez-vous aux urgences les plus proches")
            tips.append("💡 Les médecins généralistes ont souvent plus de créneaux disponibles rapidement")
            
        if params.get("specialty"):
            tips.append("💡 Essayez de chercher sans spécifier la spécialité pour voir plus d'options")
            tips.append("💡 Un médecin généraliste peut souvent vous orienter vers le bon spécialiste")
            
        if params.get("address_postalcode"):
            tips.append("💡 Élargissez votre zone de recherche aux arrondissements voisins")
            tips.append("💡 Vérifiez aussi les praticiens en téléconsultation")
            
        # Add general tips
        tips.append("💡 Contactez directement les cabinets pour connaître les disponibilités en temps réel")
        tips.append("💡 Certains praticiens acceptent les consultations sans rendez-vous")
        
        return tips[:4]  # Limit to 4 most relevant tips

    def _generate_alternative_queries(self, 
                                    original_query: str, 
                                    params: Dict[str, Any], 
                                    intent: Dict[str, bool]) -> List[str]:
        """Generate alternative query suggestions"""
        alternatives = []
        
        # Base query without specific parameters
        if params.get("specialty") and params.get("address_postalcode"):
            alternatives.append(f"Trouver un médecin généraliste à {self._format_location(params['address_postalcode'])}")
            alternatives.append(f"Chercher tous les médecins à {self._format_location(params['address_postalcode'])}")
            
        if params.get("specialty"):
            alternatives.append(f"Trouver un {params['specialty']} à Paris")
            alternatives.append("Chercher un médecin généraliste près de moi")
            
        if params.get("address_postalcode"):
            alternatives.append(f"Tous les médecins à {self._format_location(params['address_postalcode'])}")
            
        # Intent-based alternatives
        if intent.get("urgent"):
            alternatives.append("Médecin de garde près de moi")
            alternatives.append("Consultation d'urgence disponible maintenant")
            
        # Generic alternatives
        alternatives.extend([
            "Médecin disponible aujourd'hui",
            "Consultation en télémédecine",
            "Cabinet médical avec rendez-vous rapide"
        ])
        
        return alternatives[:5]

    def _format_location(self, postal_code: str) -> str:
        """Format postal code for display"""
        if postal_code.startswith("75") and len(postal_code) == 5:
            arrond = postal_code[-2:]
            return f"Paris {arrond}e"
        return postal_code

    def create_no_results_response(self, 
                                 original_query: str,
                                 parsed_params: Dict[str, Any],
                                 suggestions: Dict[str, Any]) -> str:
        """Create a user-friendly response when no results are found"""
        
        response_parts = [
            "Je n'ai pas trouvé de praticiens correspondant exactement à votre recherche.",
            ""
        ]
        
        # Add specialty alternatives
        if suggestions["specialty_alternatives"]:
            response_parts.append("**Spécialités alternatives suggérées :**")
            for alt in suggestions["specialty_alternatives"][:3]:
                response_parts.append(f"• {alt['specialty'].title()} - {alt['reason']}")
            response_parts.append("")
            
        # Add location alternatives  
        if suggestions["location_alternatives"]:
            response_parts.append("**Zones alternatives suggérées :**")
            for alt in suggestions["location_alternatives"][:3]:
                response_parts.append(f"• {alt['location']} - {alt['reason']}")
            response_parts.append("")
            
        # Add tips
        if suggestions["tips"]:
            response_parts.append("**Conseils utiles :**")
            for tip in suggestions["tips"][:3]:
                response_parts.append(tip)
            response_parts.append("")
            
        # Add alternative queries
        if suggestions["alternative_queries"]:
            response_parts.append("**Essayez ces recherches :**")
            for alt_query in suggestions["alternative_queries"][:3]:
                response_parts.append(f"• \"{alt_query}\"")
                
        return "\n".join(response_parts)
