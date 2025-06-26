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
        # Use XAI (Grok) instead of OpenAI
        xai_api_key = os.getenv("XAI_API_KEY")
        if not xai_api_key:
            raise ValueError("XAI_API_KEY environment variable is required")
        
        self.openai_client = openai.OpenAI(
            api_key=xai_api_key,
            base_url="https://api.x.ai/v1"
        )
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
   - role: Profession code (40=kinésithérapeute, 60=médecin, 86=dentiste, 31=sage-femme, 96=pharmacien, 50=ostéopathe, 23=infirmier, 95=spécialiste)
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
                model="grok-2-1212",
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
                # Handle JSON wrapped in code blocks
                content = result_text.strip()
                if content.startswith('```json'):
                    # Extract JSON from code block
                    lines = content.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip() == '```json':
                            in_json = True
                            continue
                        elif line.strip() == '```' and in_json:
                            break
                        elif in_json:
                            json_lines.append(line)
                    content = '\n'.join(json_lines)
                
                result = json.loads(content)
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
        
        # Check for medical specialties FIRST (highest priority)
        specialty_keywords = {
            'kinésithérapeute': '40', 'kiné': '40', 'kine': '40', 'physiotherapist': '40',
            'ostéopathe': '50', 'osteopath': '50', 'osteopathe': '50',
            'dentiste': '86', 'dentist': '86', 'chirurgien-dentiste': '86',
            'sage-femme': '31', 'midwife': '31', 'sages-femmes': '31',
            'pharmacien': '96', 'pharmacist': '96', 'pharmacienne': '96',
            'médecin': '60', 'medecin': '60', 'generaliste': '60', 'généraliste': '60',
            'cardiologue': '95', 'cardiologist': '95',
            'dermatologue': '95', 'dermatologist': '95',
            'infirmier': '23', 'infirmière': '23', 'nurse': '23'
        }
        
        found_specialty = None
        specialty_code = None
        for keyword, code in specialty_keywords.items():
            if keyword in query_lower:
                found_specialty = keyword
                specialty_code = code
                break
        
        # Extract postal code
        postal_match = re.search(r'\b(\d{5})\b', query)
        postal_code = postal_match.group(1) if postal_match else None
        
        # Extract city
        city_match = re.search(r'\b(paris|lyon|marseille|nice|toulouse|bordeaux|nantes)\b', query_lower)
        city = city_match.group(1).title() if city_match else None
        
        # If we found a specialty, prioritize that over name detection
        if found_specialty:
            return {
                "intent": "practitioner",
                "confidence": 0.9,
                "extracted_entities": {
                    "entity_type": ["specialist"],
                    "specialty": found_specialty,
                    "location": {
                        "city": city,
                        "postal_code": postal_code
                    }
                },
                "search_strategy": {
                    "primary": "practitioner",
                    "fallback": None,
                    "parallel": False
                },
                "fhir_params": {
                    "organization": {
                        "address-city": None,
                        "address-postalcode": None,
                        "_count": None
                    },
                    "practitioner": {
                        "specialty": specialty_code,
                        "role": specialty_code,
                        "practitioner_name": None,
                        "name": None,
                        "family": None,
                        "given": None,
                        "address-city": city,
                        "address-postalcode": postal_code,
                        "_count": "10"
                    }
                },
                "reasoning": f"Fallback rule-based interpretation - detected specialty search for {found_specialty}"
            }
        
        # Check for actual practitioner names (only if no specialty found)
        name_patterns = [
            # Pattern 1: "Dr/Doctor + name" 
            r'\b(?:dr\.?|docteur|doctor)\s+([A-ZÁÉÈÊËÏÎÔÙÛÜŸÇ][a-záéèêëïîôùûüÿç\-]+(?:\s+[A-ZÁÉÈÊËÏÎÔÙÛÜŸÇ][a-záéèêëïîôùûüÿç\-]+)+)\b',
            # Pattern 2: Proper name pattern (capitalized first+last, not specialty terms) - exclude command words at start
            r'(?:find|search|cherche|show|get|pour|pour\s+un|looking\s+for)?\s*([A-ZÁÉÈÊËÏÎÔÙÛÜŸÇ][a-záéèêëïîôùûüÿç\-]+\s+[A-ZÁÉÈÊËÏÎÔÙÛÜŸÇ][A-ZÁÉÈÊËÏÎÔÙÛÜŸÇ\-]+)\b'
        ]
        
        practitioner_name = None
        for pattern in name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                raw_name = match.group(1).strip()
                # Exclude specialty keywords from being treated as names
                if not any(spec in raw_name.lower() for spec in specialty_keywords.keys()):
                    # Exclude common command words
                    if not any(word in raw_name.lower() for word in ['find', 'search', 'cherche', 'show', 'get']):
                        practitioner_name = raw_name.title()
                        break
        
        if practitioner_name:
            # Split name into family and given
            name_parts = practitioner_name.split()
            family_name = name_parts[-1] if name_parts else ""
            given_name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else ""
            
            return {
                "intent": "practitioner",
                "confidence": 0.8,
                "extracted_entities": {
                    "entity_type": ["practitioner"],
                    "practitioner_name": practitioner_name,
                    "location": {
                        "city": city,
                        "postal_code": postal_code
                    }
                },
                "search_strategy": {
                    "primary": "practitioner",
                    "fallback": None,
                    "parallel": False
                },
                "fhir_params": {
                    "organization": {
                        "address-city": None,
                        "address-postalcode": None,
                        "_count": None
                    },
                    "practitioner": {
                        "practitioner_name": practitioner_name,
                        "name": practitioner_name,
                        "family": family_name,
                        "given": given_name,
                        "address-city": city,
                        "address-postalcode": postal_code,
                        "_count": "10"
                    }
                },
                "reasoning": f"Fallback rule-based interpretation - detected name search for {practitioner_name}"
            }
        
        # Default general search
        org_keywords = ["hospital", "hôpital", "clinic", "clinique", "cabinet", "centre", "center"]
        is_org_query = any(keyword in query_lower for keyword in org_keywords)
        intent = "organization" if is_org_query else "practitioner"
        
        return {
            "intent": intent,
            "confidence": 0.6,
            "extracted_entities": {
                "entity_type": ["organization"] if intent == "organization" else ["practitioner"],
                "location": {
                    "city": city,
                    "postal_code": postal_code
                }
            },
            "search_strategy": {
                "primary": intent,
                "fallback": None,
                "parallel": False
            },
            "fhir_params": {
                "organization": {
                    "address-city": city if intent == "organization" else None,
                    "address-postalcode": postal_code if intent == "organization" else None,
                    "_count": "10"
                },
                "practitioner": {
                    "address-city": city if intent == "practitioner" else None,
                    "address-postalcode": postal_code if intent == "practitioner" else None,
                    "_count": "10"
                }
            },
            "reasoning": f"Fallback rule-based interpretation - general {intent} search"
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
            "practitioner_name": "value or null",
            "name": "value or null", 
            "family": "value or null",
            "given": "value or null",
            "address-city": "value or null",
            "address-postalcode": "value or null", 
            "_count": "number"
        }}
    }},
    "reasoning": "Brief explanation of your interpretation"
}}

Handle French language naturally. Convert Paris arrondissements to postal codes.
Be intelligent about ambiguous queries - use context clues.
For name searches, extract the practitioner name and put it in the practitioner_name field.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="grok-2-1212",
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
                # Handle JSON wrapped in code blocks
                content = result_text.strip()
                if content.startswith('```json'):
                    # Extract JSON from code block
                    lines = content.split('\n')
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.strip() == '```json':
                            in_json = True
                            continue
                        elif line.strip() == '```' and in_json:
                            break
                        elif in_json:
                            json_lines.append(line)
                    content = '\n'.join(json_lines)
                
                result = json.loads(content)
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
