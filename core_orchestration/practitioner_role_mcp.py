import requests
import re
import difflib
import sys
import os
from typing import Dict, Any

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.base_mcp import BaseMCP
from backend.core.intent_parser import IntentParser
from routers.sante import PROFESSION_SANTE_CODE_TO_LABEL, PROFESSION_SANTE_LABEL_TO_CODE

# Paris arrondissement to postal code mapping
PARIS_ARR_MAP = {
    "1er": "75001", "2e": "75002", "3e": "75003", "4e": "75004", "5e": "75005",
    "6e": "75006", "7e": "75007", "8e": "75008", "9e": "75009", "10e": "75010",
    "11e": "75011", "12e": "75012", "13e": "75013", "14e": "75014", "15e": "75015",
    "16e": "75016", "17e": "75017", "18e": "75018", "19e": "75019", "20e": "75020",
    # English variations
    "1st": "75001", "2nd": "75002", "3rd": "75003", "4th": "75004", "5th": "75005",
    "6th": "75006", "7th": "75007", "8th": "75008", "9th": "75009", "10th": "75010",
    "11th": "75011", "12th": "75012", "13th": "75013", "14th": "75014", "15th": "75015",
    "16th": "75016", "17th": "75017", "18th": "75018", "19th": "75019", "20th": "75020"
}

# Specialty mapping
SPECIALTY_MAP = {
    "generaliste": "60",
    "medecin generaliste": "60",
    "general practitioner": "60",
    "gp": "60",
    "specialist": "95",
    "medecin specialiste": "95",
    "dentist": "86",
    "dentiste": "86",
    "chirurgien-dentiste": "86",
    "sage-femme": "31",
    "midwife": "31",
    "pharmacien": "96",
    "pharmacist": "96",
    "anesthesiste": "34",
    "anesthesiologist": "34",
    "dermatologue": "33",
    "dermatologist": "33",
    "allergologue": "36",
    "allergist": "36",
    "chiropracteur": "54",
    "chiropractor": "54",
    "pediatre": "77",
    "pediatrician": "77",
    "cardiologue": "38",
    "cardiologist": "38",
    "gastroenterologue": "40",
    "gastroenterologist": "40",
    "endocrinologue": "37",
    "endocrinologist": "37"
}

# English to French specialty translations
ENGLISH_TO_FRENCH_SPECIALTY = {
    "general practitioner": "generaliste",
    "gp": "generaliste",
    "specialist": "specialiste",
    "dentist": "dentiste",
    "midwife": "sage-femme",
    "pharmacist": "pharmacien",
    "anesthesiologist": "anesthesiste",
    "dermatologist": "dermatologue",
    "allergist": "allergologue",
    "chiropractor": "chiropracteur",
    "pediatrician": "pediatre",
    "cardiologist": "cardiologue",
    "gastroenterologist": "gastroenterologue",
    "endocrinologist": "endocrinologue"
}

class PractitionerRoleMCP(BaseMCP):
    def __init__(self):
        self.paris_arr_map = PARIS_ARR_MAP
        self.specialty_map = SPECIALTY_MAP
        self.english_to_french = ENGLISH_TO_FRENCH_SPECIALTY
        self.intent_parser = IntentParser()

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "intents": ["find_practitioner", "find_doctor", "find_healthcare_provider"],
            "entities": ["specialty", "postal_code", "name", "active", "role"],
            "confidence_threshold": 0.5
        }

    def _fuzzy_specialty_match(self, phrase: str) -> str:
        """Internal method for fuzzy matching specialties"""
        all_keys = set(self.specialty_map.keys()) | set(self.english_to_french.keys())
        tokens = [t for t in re.split(r"[\s,]+", phrase.lower()) if t]

        for token in tokens:
            if token in self.specialty_map:
                return self.specialty_map[token]
            if token in self.english_to_french:
                fr = self.english_to_french[token]
                if fr in self.specialty_map:
                    return self.specialty_map[fr]

            close = difflib.get_close_matches(token, all_keys, n=1, cutoff=0.8)
            if close:
                match = close[0]
                if match in self.specialty_map:
                    return self.specialty_map[match]
                elif match in self.english_to_french:
                    fr = self.english_to_french[match]
                    if fr in self.specialty_map:
                        return self.specialty_map[fr]
        return None

    def _parse_query_params(self, query: str) -> Dict[str, Any]:
        """Extract query parameters from natural language query"""
        params = {}
        
        # Try fuzzy specialty matching
        specialty = self._fuzzy_specialty_match(query)
        if specialty:
            params["specialty"] = specialty
            
        # Extract postal code/arrondissement
        postal_code = None
        
        # Try Paris arrondissement patterns
        # Look for "paris 17th", "17th arrondissement", "paris 17e", etc.
        m = re.search(r"paris[\s-]*(\d{1,2})(?:er|e|ème|th|st|nd|rd)?(?:\s+arrondissement)?", query.lower())
        if m:
            num = int(m.group(1))
            if 1 <= num <= 20:
                postal_code = f"750{num:02d}"
        
        # Try exact mapping keys
        if not postal_code:
            for arr, code in self.paris_arr_map.items():
                if arr in query.lower():
                    postal_code = code
                    break
        
        # Try direct postal code pattern
        if not postal_code:
            m = re.search(r"(\d{5})", query)
            if m:
                postal_code = m.group(1)
                
        if postal_code:
            params["address-postalcode"] = postal_code
            
        # Extract count
        count_match = re.search(r"(\d+)", query)
        count = int(count_match.group(1)) if count_match else 5
        
        return params, count

    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a natural language query to search for practitioners"""
        try:
            # Parse query parameters
            params, count = self._parse_query_params(query)
            
            # Call backend API
            endpoint = "http://localhost:8000/api/practitionerrole/search"
            print(f"[DEBUG] Querying {endpoint} with params {params}")
            
            resp = requests.get(endpoint, params=params)
            resp.raise_for_status()
            bundle = resp.json()
            
            roles = bundle.get("entry", [])[:count]
            
            if not roles:
                return {
                    "message": "No practitioners found matching your criteria.",
                    "success": True,
                    "data": {"results": [], "query_params": params}
                }

            results = []
            for item in roles:
                pr = item.get("resource", item)
                results.append({
                    "name": pr.get("name", "Unknown"),
                    "specialty": pr.get("specialite_label", pr.get("specialite", "Unknown")),
                    "active": pr.get("active", True),
                    "id": pr.get("id", "unknown")
                })

            return {
                "message": f"Found {len(results)} practitioners",
                "success": True,
                "data": {"results": results, "query_params": params}
            }

        except Exception as e:
            return {
                "message": f"Failed to process query: {str(e)}",
                "success": False,
                "data": {"error": str(e)}
            }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        query = sys.argv[1]
        mcp = PractitionerRoleMCP()
        result = mcp.process_query(query)
        print(result)
    else:
        print("Usage: python practitioner_role_mcp.py 'your query here'")
        print("Example: python practitioner_role_mcp.py 'find a sage-femme in paris 17th'")
