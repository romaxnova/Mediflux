"""
AI-Powered Query Interpreter for Healthcare Search
Intelligently parses user queries and maps them to FHIR API parameters
"""

import openai
import json
import os
from typing import Dict, List, Any, Optional
import re

class AIQueryInterpreter:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.fhir_context = self._load_fhir_context()
    
    def _load_fhir_context(self) -> str:
        """Load FHIR API context for the AI to understand available parameters"""
        return """
FHIR API Context for French Healthcare Directory:

ORGANIZATION SEARCH (https://gateway.api.esante.gouv.fr/fhir/Organization):
- name: Organization name (use specific organization names, avoid generic terms like "hôpital")
- address-city: City name (preferred over postal codes for broader search)
- address-postalcode: Postal code (75001, 13001, etc.)
- type: Organization type
- active: true/false
- _count: Number of results
- NOTE: Generic terms like "hôpital", "clinique" in name parameter cause timeouts. Use city-based search instead.

PRACTITIONER SEARCHES:
1. BY SPECIALTY (PractitionerRole): Use role parameter for profession-based searches
   - role: Profession code (40=kinésithérapeute, 60=médecin, 86=dentiste, etc.)
   - address-postalcode: Postal code
   - address-city: City name (local filtering)
   - _count: Number of results
   
2. BY NAME (Practitioner): Use name parameters for name-based searches  
   - name: Full name search
   - family: Last name only
   - given: First name only
   - _count: Number of results

FRENCH CONTEXT:
- Paris arrondissements: 1er, 2e, ..., 20e → 75001, 75002, ..., 75020
- Common terms: hôpital=hospital, clinique=clinic, cabinet=practice, centre médical=medical center
- Specialties: cardiologue=cardiologist, dentiste=dentist, sage-femme=midwife, etc.
- IMPORTANT: For organization searches, prefer geographic filters over generic type names
"""

    async def interpret_query(self, user_query: str) -> Dict[str, Any]:
        """
        Use AI to intelligently interpret user query and generate search strategy
        """
        
        system_prompt = f"""You are an intelligent healthcare search interpreter for France. 
Your job is to analyze user queries and determine the best search strategy.

{self.fhir_context}

Analyze the user query and return a JSON response with this structure:
{{
    "intent": "organization" | "practitioner" | "mixed",
    "confidence": 0.0-1.0,
    "extracted_entities": {{
        "entity_type": ["hospital", "clinic", "doctor", "specialist", etc.],
        "specialty": "extracted medical specialty if any",
        "location": {{
            "city": "city name if mentioned",
            "postal_code": "postal code if extractable",
            "arrondissement": "Paris arrondissement if mentioned"
        }},
        "organization_name": "specific name if mentioned",
        "practitioner_name": "specific name if mentioned",
        "count": "number if user specified how many results"
    }},
    "search_strategy": {{
        "primary": "organization" | "practitioner",
        "fallback": "organization" | "practitioner" | null,
        "parallel": true | false
    }},
    "fhir_params": {{
        "organization": {{
            "name": "value or null",
            "address-city": "value or null", 
            "address-postalcode": "value or null",
            "_count": "number"
        }},
        "practitioner": {{
            "specialty": "value or null",
            "address-city": "value or null",
            "address-postalcode": "value or null", 
            "_count": "number"
        }}
    }},
    "reasoning": "Brief explanation of your interpretation"
}}

Handle French language naturally. Convert Paris arrondissements to postal codes.
Be intelligent about ambiguous queries - use context clues.
"""

        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {user_query}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                result = json.loads(result_text)
                print(f"[AI_DEBUG] Interpreted query: {user_query}")
                print(f"[AI_DEBUG] Result: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"[AI_ERROR] Failed to parse AI response: {e}")
                print(f"[AI_ERROR] Raw response: {result_text}")
                return self._fallback_interpretation(user_query)
                
        except Exception as e:
            print(f"[AI_ERROR] AI interpretation failed: {e}")
            return self._fallback_interpretation(user_query)
    
    def _fallback_interpretation(self, query: str) -> Dict[str, Any]:
        """Fallback to simple rule-based interpretation if AI fails"""
        query_lower = query.lower()
        
        # Simple organization keywords
        org_keywords = ["hospital", "hôpital", "clinic", "clinique", "cabinet", "centre", "center"]
        is_org_query = any(keyword in query_lower for keyword in org_keywords)
        
        # Extract postal code
        postal_match = re.search(r'\b(\d{5})\b', query)
        postal_code = postal_match.group(1) if postal_match else None
        
        # Extract city
        city_match = re.search(r'\b(paris|lyon|marseille|nice|toulouse|bordeaux|nantes)\b', query_lower)
        city = city_match.group(1).title() if city_match else None
        
        return {
            "intent": "organization" if is_org_query else "practitioner",
            "confidence": 0.6,
            "extracted_entities": {
                "entity_type": ["organization"] if is_org_query else ["practitioner"],
                "location": {
                    "city": city,
                    "postal_code": postal_code
                }
            },
            "search_strategy": {
                "primary": "organization" if is_org_query else "practitioner",
                "fallback": None,
                "parallel": False
            },
            "fhir_params": {
                "organization": {
                    "address-city": city if is_org_query else None,
                    "address-postalcode": postal_code if is_org_query else None,
                    "_count": "10"
                },
                "practitioner": {
                    "address-city": city if not is_org_query else None,
                    "address-postalcode": postal_code if not is_org_query else None,
                    "_count": "10"
                }
            },
            "reasoning": "Fallback rule-based interpretation"
        }
    
    def synchronous_interpret_query(self, user_query: str) -> Dict[str, Any]:
        """Synchronous version using regular OpenAI client"""
        system_prompt = f"""You are an intelligent healthcare search interpreter for France. 
Your job is to analyze user queries and determine the best search strategy.

{self.fhir_context}

Analyze the user query and return a JSON response with this structure:
{{
    "intent": "organization" | "practitioner" | "mixed",
    "confidence": 0.0-1.0,
    "extracted_entities": {{
        "entity_type": ["hospital", "clinic", "doctor", "specialist", etc.],
        "specialty": "extracted medical specialty if any",
        "location": {{
            "city": "city name if mentioned",
            "postal_code": "postal code if extractable",
            "arrondissement": "Paris arrondissement if mentioned"
        }},
        "organization_name": "specific name if mentioned",
        "practitioner_name": "specific name if mentioned",
        "count": "number if user specified how many results"
    }},
    "search_strategy": {{
        "primary": "organization" | "practitioner",
        "fallback": "organization" | "practitioner" | null,
        "parallel": true | false
    }},
    "fhir_params": {{
        "organization": {{
            "name": "value or null",
            "address-city": "value or null", 
            "address-postalcode": "value or null",
            "_count": "number"
        }},
        "practitioner": {{
            "specialty": "value or null",
            "address-city": "value or null",
            "address-postalcode": "value or null", 
            "_count": "number"
        }}
    }},
    "reasoning": "Brief explanation of your interpretation"
}}

Handle French language naturally. Convert Paris arrondissements to postal codes.
Be intelligent about ambiguous queries - use context clues.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {user_query}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                result = json.loads(result_text)
                print(f"[AI_DEBUG] Interpreted query: {user_query}")
                print(f"[AI_DEBUG] Result: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"[AI_ERROR] Failed to parse AI response: {e}")
                print(f"[AI_ERROR] Raw response: {result_text}")
                return self._fallback_interpretation(user_query)
                
        except Exception as e:
            print(f"[AI_ERROR] AI interpretation failed: {e}")
            return self._fallback_interpretation(user_query)
