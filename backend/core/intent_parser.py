import re
import difflib
from typing import Dict, Any, Optional, Tuple
from .data.specialties import SPECIALTY_MAP, SPECIALTY_VARIATIONS

class IntentParser:
    @staticmethod
    def fuzzy_match(query: str, options: list, cutoff: float = 0.6) -> Tuple[Optional[str], float]:
        """
        Fuzzy matches a query against a list of options.
        Returns a tuple of (matched_string, confidence_score).
        """
        # Try exact match first
        lower_query = query.lower()
        lower_options = {opt.lower(): opt for opt in options}
        if lower_query in lower_options:
            return lower_options[lower_query], 1.0

        # Try fuzzy matching
        matches = difflib.get_close_matches(lower_query, lower_options.keys(), n=1, cutoff=cutoff)
        if matches:
            score = difflib.SequenceMatcher(None, lower_query, matches[0]).ratio()
            return lower_options[matches[0]], score

        return None, 0.0

    @staticmethod
    def extract_specialty(query: str) -> Tuple[Optional[str], float]:
        """
        Extract medical specialty from query with confidence score.
        Handles both French and English terms, variations, and misspellings.
        """
        # First check variations to handle common misspellings and abbreviations
        lower_query_words = query.lower().split()
        for i in range(len(lower_query_words)):
            for j in range(i + 1, len(lower_query_words) + 1):
                phrase = " ".join(lower_query_words[i:j])
                if phrase in SPECIALTY_VARIATIONS:
                    normalized = SPECIALTY_VARIATIONS[phrase]
                    return SPECIALTY_MAP.get(normalized), 1.0

        # Try fuzzy matching against all specialties
        best_match, confidence = IntentParser.fuzzy_match(query, list(SPECIALTY_MAP.keys()))
        if best_match:
            return best_match, confidence
        
        return None, 0.0

    @staticmethod
    def extract_location(query: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Extract location information from query.
        Returns (postal_code, city, confidence).
        """
        confidence = 0.0
        postal_code = None
        city = None

        # Try postal code patterns
        postal_patterns = [
            # Direct postal code
            r"(?:at|in|from)?\s*(\d{5})\b",
            # Paris arrondissement - various formats
            r"paris\s*(\d{1,2})(?:er|e|ème|th|st|nd|rd)?\s*(?:arr)?(?:ondissement)?",
            r"(?:at|in|from)?\s*(?:the\s*)?(\d{1,2})(?:er|e|ème|th|st|nd|rd)?\s*(?:arr)?(?:ondissement)?(?:\s*of)?\s*paris",
        ]

        for pattern in postal_patterns:
            m = re.search(pattern, query, re.IGNORECASE)
            if m:
                if len(m.group(1)) == 5:  # Direct postal code
                    postal_code = m.group(1)
                    confidence = 1.0
                else:  # Arrondissement
                    num = int(m.group(1))
                    if 1 <= num <= 20:
                        postal_code = f"750{num:02d}"
                        confidence = 1.0
                break

        # Extract city name if present
        city_match = re.search(r"(?:at|in|from)?\s*(paris|lyon|marseille|bordeaux|toulouse|nantes|strasbourg|lille|rennes|reims)", query, re.IGNORECASE)
        if city_match:
            city = city_match.group(1).title()
            confidence = max(confidence, 0.8)

        return postal_code, city, confidence

    @staticmethod
    def parse(query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into structured intent and entities.
        Handles both French and English queries for healthcare domain.

        Returns:
            Dict containing:
            - type: The type of query (find_practitioner, find_organization)
            - entities: Extracted information (specialty, location, etc)
            - confidence: Confidence score (0-1)
            - fallback: Whether fallback handling is needed
            - raw_query: Original query text
        """
        intent = {
            "type": "unknown",
            "entities": {},
            "confidence": 0.0,
            "fallback": False,
            "raw_query": query
        }

        # Extract count if present
        count_match = re.search(r"(?:find|get|show me|list)\s+(\d+)", query.lower())
        if count_match:
            intent["entities"]["count"] = int(count_match.group(1))
            intent["confidence"] += 0.1

        # Basic intent detection and entity extraction
        healthcare_keywords = [
            "find", "doctor", "practitioner", "médecin", "docteur", "sage-femme", "midwife",
            "dentiste", "dentist", "pharmacien", "pharmacist", "infirmier", "nurse",
            "kinésithérapeute", "physiotherapist", "ostéopathe", "osteopath"
        ]
        
        if any(keyword in query.lower() for keyword in healthcare_keywords):
            intent["type"] = "find_practitioner"

            # Extract specialty
            specialty, spec_confidence = IntentParser.extract_specialty(query)
            if specialty:
                intent["entities"]["specialty"] = specialty
                intent["confidence"] += 0.3 * spec_confidence

            # Extract location
            postal_code, city, loc_confidence = IntentParser.extract_location(query)
            if postal_code:
                intent["entities"]["postal_code"] = postal_code
                intent["confidence"] += 0.3 * loc_confidence
            if city:
                intent["entities"]["city"] = city
                intent["confidence"] += 0.2 * loc_confidence

            # Handle professional role indicators
            if any(term in query.lower() for term in ["doctor", "docteur", "médecin", "practitioner", "praticien"]):
                intent["entities"]["role"] = "practitioner"
                intent["confidence"] += 0.2

            # Boost confidence for specific healthcare professionals
            specific_roles = ["sage-femme", "midwife", "dentiste", "dentist", "pharmacien", "pharmacist"]
            if any(role in query.lower() for role in specific_roles):
                intent["confidence"] += 0.4

            # Overall confidence adjustments
            if len(intent["entities"]) >= 2:  # Has at least specialty/location + role
                intent["confidence"] = min(1.0, intent["confidence"] + 0.1)  # Bonus for multiple entities

        elif any(keyword in query.lower() for keyword in ["organization", "hospital", "clinic", "hôpital", "clinique"]):
            intent["type"] = "find_organization"
            # Extract location for organizations
            postal_code, city, loc_confidence = IntentParser.extract_location(query)
            if postal_code:
                intent["entities"]["postal_code"] = postal_code
                intent["confidence"] += 0.4 * loc_confidence
            if city:
                intent["entities"]["city"] = city
                intent["confidence"] += 0.3 * loc_confidence

            # Look for organization type indicators
            org_types = ["hospital", "clinic", "laboratory", "hôpital", "clinique", "laboratoire"]
            for org_type in org_types:
                if org_type in query.lower():
                    intent["entities"]["type"] = org_type
                    intent["confidence"] += 0.3
                    break

        # Normalize confidence and set fallback flag
        intent["confidence"] = min(1.0, intent["confidence"])
        if intent["confidence"] < 0.5 or not intent["entities"]:
            intent["fallback"] = True
            intent["confidence"] = max(0.1, intent["confidence"])  # Minimum confidence for fallback
        return intent
