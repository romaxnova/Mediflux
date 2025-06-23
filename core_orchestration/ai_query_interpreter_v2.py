"""
Enhanced AI-Powered Query Interpreter for Healthcare Search
Intelligently parses user queries and maps them to all 5 FHIR resources efficiently
"""

import openai
import json
import os
from typing import Dict, List, Any, Optional
import re

class EnhancedAIQueryInterpreter:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.fhir_context = self._load_comprehensive_fhir_context()
    
    def _load_comprehensive_fhir_context(self) -> str:
        """Load comprehensive FHIR API context covering all 5 resources"""
        return """
COMPREHENSIVE FHIR API CONTEXT for French Healthcare Directory:

BASE URL: https://gateway.api.esante.gouv.fr/fhir/
AUTHENTICATION: Header 'ESANTE-API-KEY: {api_key}'

=== 5 MAIN RESOURCES ===

1. ORGANIZATION (Healthcare facilities):
   - Endpoint: /Organization
   - Parameters: name, address-city, address-postalcode, type, active, _count
   - Use for: hospitals, clinics, pharmacies, medical centers
   - Strategy: Use address-city for geographic searches, avoid generic terms in name

2. PRACTITIONER ROLE (Professionals in context):
   - Endpoint: /PractitionerRole  
   - Parameters: role (profession code), organization, location, active, _count
   - Profession codes: 60=médecin, 40=kinésithérapeute, 86=dentiste, 31=sage-femme, 96=pharmacien
   - Use for: finding professionals by specialty/profession
   - Note: Display names often null, use role codes for filtering

3. PRACTITIONER (Individual professionals):
   - Endpoint: /Practitioner
   - Parameters: name, family, given, identifier, active, _count
   - Use for: finding professionals by name (first/last name searches)
   - Best for: "find Dr. Smith", "cherche Jean Dupont"

4. HEALTHCARE SERVICE (Specific services):
   - Endpoint: /HealthcareService
   - Parameters: organization, location, service-category, service-type, active, _count
   - Use for: emergency services, radiology, laboratory, specific medical services

5. DEVICE (Medical equipment):
   - Endpoint: /Device
   - Parameters: organization, location, type, status, _count
   - Use for: MRI machines, CT scanners, medical equipment

=== SEARCH STRATEGIES ===

QUERY TYPE DETECTION:
- Organization: "hôpital", "clinique", "centre médical", "pharmacie"
- Practitioner by specialty: "cardiologue", "dentiste", "médecin généraliste" 
- Practitioner by name: "Dr. Martin", "Jean Dupont", specific person names
- Services: "urgences", "radiologie", "laboratoire", "service de..."
- Equipment: "IRM", "scanner", "équipement médical"

GEOGRAPHIC HANDLING:
- Paris arrondissements: 1er, 2e, ..., 20e → 75001, 75002, ..., 75020
- Use address-city for broad searches, address-postalcode for precise location
- Cities: Paris, Lyon, Marseille, Nice, Toulouse, Bordeaux, Nantes, etc.

PROFESSION CODES (TRE-G15-ProfessionSante):
- 60: Médecin généraliste, most medical specialists
- 40: Kinésithérapeute
- 86: Dentiste, Chirurgien-dentiste  
- 31: Sage-femme
- 96: Pharmacien
- 23: Infirmier
- 50: Ostéopathe

SEARCH OPTIMIZATION:
- Use specific resource for specific needs
- Combine multiple resources for comprehensive results
- Parallel searches when appropriate
- Local filtering for complex geographic queries
"""

    def synchronous_interpret_query(self, user_query: str) -> Dict[str, Any]:
        """Enhanced synchronous interpretation using all 5 FHIR resources"""
        system_prompt = f"""You are an intelligent French healthcare search interpreter with access to 5 FHIR resources.

{self.fhir_context}

Analyze the user query and return a JSON response with this structure:
{{
    "intent": "organization" | "practitioner_role" | "practitioner_name" | "healthcare_service" | "device" | "mixed",
    "confidence": 0.0-1.0,
    "extracted_entities": {{
        "entity_type": ["hospital", "clinic", "doctor", "specialist", "service", "equipment", etc.],
        "specialty": "extracted medical specialty if any",
        "service_type": "specific service if mentioned",
        "equipment_type": "medical equipment if mentioned",
        "location": {{
            "city": "city name if mentioned",
            "postal_code": "postal code if extractable", 
            "arrondissement": "Paris arrondissement if mentioned"
        }},
        "organization_name": "specific organization name if mentioned",
        "practitioner_name": "specific person name if mentioned",
        "count": "number if user specified how many results"
    }},
    "search_strategy": {{
        "primary": "organization" | "practitioner_role" | "practitioner_name" | "healthcare_service" | "device",
        "secondary": ["list of fallback resources"] | null,
        "parallel": true | false,
        "reasoning": "why this strategy was chosen"
    }},
    "fhir_params": {{
        "organization": {{
            "name": "value or null",
            "address-city": "value or null",
            "address-postalcode": "value or null", 
            "type": "value or null",
            "_count": "number"
        }},
        "practitioner_role": {{
            "role": "profession code or null",
            "organization": "reference or null",
            "active": "true or null",
            "_count": "number"
        }},
        "practitioner_name": {{
            "name": "full name or null",
            "family": "last name or null",
            "given": "first name or null",
            "_count": "number"
        }},
        "healthcare_service": {{
            "service-category": "value or null",
            "service-type": "value or null", 
            "organization": "reference or null",
            "_count": "number"
        }},
        "device": {{
            "type": "value or null",
            "organization": "reference or null",
            "_count": "number"
        }}
    }},
    "reasoning": "Brief explanation of interpretation and strategy"
}}

EXAMPLES:
- "hôpital à Paris" → organization search with address-city=Paris
- "cardiologue à Lyon" → practitioner_role search with role=60, local filter Lyon
- "Dr. Martin" → practitioner_name search with name=Martin
- "service d'urgences" → healthcare_service search with service-category=emergency
- "IRM à Marseille" → device search with type=MRI + organization filter

Handle French language naturally. Be intelligent about ambiguous queries.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {user_query}"}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content
            
            try:
                result = json.loads(result_text)
                print(f"[AI_V2_DEBUG] Interpreted query: {user_query}")
                print(f"[AI_V2_DEBUG] Result: {result}")
                
                # Validate and enhance the result
                result = self._validate_and_enhance_result(result, user_query)
                return result
                
            except json.JSONDecodeError as e:
                print(f"[AI_V2_ERROR] Failed to parse AI response: {e}")
                print(f"[AI_V2_ERROR] Raw response: {result_text}")
                return self._comprehensive_fallback_interpretation(user_query)
                
        except Exception as e:
            print(f"[AI_V2_ERROR] AI interpretation failed: {e}")
            return self._comprehensive_fallback_interpretation(user_query)
    
    def _validate_and_enhance_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Validate and enhance AI interpretation result"""
        
        # Ensure required fields exist
        if "intent" not in result:
            result["intent"] = "organization"
        if "confidence" not in result:
            result["confidence"] = 0.7
        if "search_strategy" not in result:
            result["search_strategy"] = {"primary": result["intent"], "parallel": False}
        if "fhir_params" not in result:
            result["fhir_params"] = {}
            
        # Enhance geographic data
        location = result.get("extracted_entities", {}).get("location", {})
        if location.get("arrondissement"):
            # Convert Paris arrondissement to postal code
            arr_match = re.search(r'(\d+)', location["arrondissement"])
            if arr_match:
                arr_num = int(arr_match.group(1))
                if 1 <= arr_num <= 20:
                    postal_code = f"7500{arr_num:d}" if arr_num >= 10 else f"7500{arr_num:d}"
                    location["postal_code"] = postal_code
                    location["city"] = "Paris"
        
        # Ensure profession code mapping
        specialty = result.get("extracted_entities", {}).get("specialty", "")
        if specialty and result.get("intent") == "practitioner_role":
            profession_codes = {
                "généraliste": "60", "médecin": "60", "cardiologue": "60",
                "kinésithérapeute": "40", "kiné": "40", "kine": "40",
                "dentiste": "86", "sage-femme": "31", "pharmacien": "96"
            }
            
            for term, code in profession_codes.items():
                if term in specialty.lower():
                    if "practitioner_role" not in result["fhir_params"]:
                        result["fhir_params"]["practitioner_role"] = {}
                    result["fhir_params"]["practitioner_role"]["role"] = code
                    break
        
        return result
    
    def _comprehensive_fallback_interpretation(self, query: str) -> Dict[str, Any]:
        """Enhanced fallback interpretation covering all resources"""
        query_lower = query.lower()
        
        # Resource detection patterns
        org_patterns = ["hôpital", "hopital", "clinique", "centre", "pharmacie", "cabinet"]
        practitioner_specialty_patterns = ["médecin", "medecin", "cardiologue", "dentiste", "kinésithérapeute", "sage-femme"]
        practitioner_name_patterns = ["dr.", "docteur", "prof.", "professeur"]
        service_patterns = ["service", "urgence", "radiologie", "laboratoire"]
        device_patterns = ["irm", "scanner", "équipement", "equipement"]
        
        # Determine primary intent
        intent = "organization"  # default
        if any(pattern in query_lower for pattern in practitioner_name_patterns):
            intent = "practitioner_name"
        elif any(pattern in query_lower for pattern in practitioner_specialty_patterns):
            intent = "practitioner_role"
        elif any(pattern in query_lower for pattern in service_patterns):
            intent = "healthcare_service"
        elif any(pattern in query_lower for pattern in device_patterns):
            intent = "device"
        elif any(pattern in query_lower for pattern in org_patterns):
            intent = "organization"
        
        # Extract geographic info
        postal_match = re.search(r'\b(\d{5})\b', query)
        postal_code = postal_match.group(1) if postal_match else None
        
        city_match = re.search(r'\b(paris|lyon|marseille|nice|toulouse|bordeaux|nantes|lille|rennes|strasbourg)\b', query_lower)
        city = city_match.group(1).title() if city_match else None
        
        # Build fallback result
        return {
            "intent": intent,
            "confidence": 0.6,
            "extracted_entities": {
                "entity_type": [intent.replace("_", " ")],
                "location": {
                    "city": city,
                    "postal_code": postal_code
                }
            },
            "search_strategy": {
                "primary": intent,
                "parallel": False,
                "reasoning": "Fallback rule-based interpretation"
            },
            "fhir_params": self._build_fallback_params(intent, city, postal_code),
            "reasoning": "Fallback interpretation due to AI parsing failure"
        }
    
    def _build_fallback_params(self, intent: str, city: str, postal_code: str) -> Dict[str, Any]:
        """Build FHIR parameters for fallback interpretation"""
        params = {
            "organization": {"_count": "10"},
            "practitioner_role": {"_count": "10"}, 
            "practitioner_name": {"_count": "10"},
            "healthcare_service": {"_count": "10"},
            "device": {"_count": "10"}
        }
        
        # Add location parameters where applicable
        if city:
            if intent == "organization":
                params["organization"]["address-city"] = city
        
        if postal_code:
            if intent == "organization":
                params["organization"]["address-postalcode"] = postal_code
        
        return params
