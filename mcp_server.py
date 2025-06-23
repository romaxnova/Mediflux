# System imports
import json
import os
import re
import traceback

# Third-party imports
import httpx
import openai
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Local imports
from backend.core.orchestrator import HealthcareOrchestrator
from core_orchestration.organization_mcp import OrganizationMCP
from core_orchestration.practitioner_role_mcp import PractitionerRoleMCP

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7000", "http://127.0.0.1:7000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestrator with MCPs
orchestrator = HealthcareOrchestrator()
orchestrator.register_mcp("practitioner", PractitionerRoleMCP())
orchestrator.register_mcp("organization", OrganizationMCP())

# Load API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANNUAIRE_SANTE_API_KEY = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")  # Default test key
ANNUAIRE_SANTE_BASE_URL = os.getenv("ANNUAIRE_SANTE_BASE_URL", "https://gateway.api.esante.gouv.fr/annuaire-sante/v2")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.openai.com/v1/")

# Load tool schema for LLM prompt
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "mcp.organization.json")
with open(SCHEMA_PATH, "r") as f:
    tool_schema = json.load(f)

class QueryRequest(BaseModel):
    query: str

@app.post("/mcp/organization_context")
def mcp_organization_context(req: QueryRequest):
    try:
        print(f"[DEBUG] Organization context query: {req.query}")
        # Create organization MCP instance directly to avoid orchestrator issues
        org_mcp = OrganizationMCP()
        result = org_mcp.process_query(req.query)
        print(f"[DEBUG] Organization MCP result: {result}")
        return {"result": result}
    except Exception as e:
        print(f"[ERROR] Organization context error: {str(e)}")
        return {"result": {"success": False, "error": str(e), "results": []}}

@app.get("/api/practitionerrole/search")
async def practitioner_role_search(specialty: str = None, address_postalcode: str = None):
    """API endpoint for PractitionerRole search with FHIR parameters"""
    params = {}
    headers = {
        "Authorization": f"Bearer {ANNUAIRE_SANTE_API_KEY}",
        "Accept": "application/json"
    }

    if specialty:
        params["specialty"] = specialty
    if address_postalcode:
        params["address-postalcode"] = address_postalcode

    # Use mock data for testing until we have real API access
    mock_data = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "PractitionerRole",
                    "id": "test1",
                    "name": "Dr. Jean Dupont",
                    "specialty": specialty,
                    "extension": [
                        {
                            "url": "http://fhir.fr/address",
                            "valueString": f"{address_postalcode} Paris"
                        }
                    ],
                    "active": True
                }
            }
        ]
    }

    try:
        # For now, return mock data
        return mock_data
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] PractitionerRole HTTP error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        print(f"[ERROR] PractitionerRole search failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

@app.post("/mcp/practitioner_role_context")
def mcp_practitioner_role_context(req: QueryRequest):
    prac_mcp = orchestrator.mcp_registry.get_mcp("practitioner")
    return {"result": prac_mcp.process_query(req.query)}

@app.post("/mcp/execute")
async def mcp_execute(request: Request):
    """Enhanced MCP execution with AI-powered orchestration"""
    body = await request.json()
    query = body.get("prompt") or body.get("query") or ""

    try:
        print(f"[DEBUG] Enhanced MCP processing query: {query}")
        
        # Use the enhanced orchestrator with AI interpretation
        result = orchestrator.process_query(query)
        
        print(f"[DEBUG] Orchestrator result: {result.get('success', False)}")
        
        # Format response to match expected structure
        response = {
            "choices": [
                {
                    "message": {
                        "content": result.get("message", "No results found")
                    },
                    "data": {
                        "natural_response": result.get("natural_response", result.get("message", "No results found")),
                        "structured_data": result.get("structured_data", {"success": False, "data": {"results": []}}),
                        "success": result.get("success", False)
                    }
                }
            ]
        }
        
        return response
        
    except Exception as e:
        print(f"[ERROR] MCP execute failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "choices": [
                {
                    "message": {
                        "content": f"API error: {str(e)}"
                    },
                    "data": {
                        "natural_response": f"API error: {str(e)}",
                        "structured_data": {
                            "success": False,
                            "message": f"API error: {str(e)}",
                            "data": {"results": []}
                        },
                        "success": False
                    }
                }
            ]
        }

# Simple role code mapping (from our testing)
ROLE_CODES = {
    # General practitioners
    "generaliste": "60",
    "généraliste": "60",
    "médecin": "60", 
    "medecin": "60",
    "médecin généraliste": "60",
    "medecin generaliste": "60",
    "general practitioner": "60",
    "doctor": "60",
    
    # Specialists (most use code 95)
    "cardiologue": "95",
    "cardiologist": "95",
    "dermatologue": "95", 
    "dermatologist": "95",
    "psychiatre": "95",
    "psychiatrist": "95",
    "gynécologue": "95",
    "gynécologiste": "95",
    "gynecologist": "95",
    "ophtalmologiste": "95",
    "ophthalmologist": "95",
    "urologue": "95",
    "urologist": "95",
    "neurologue": "95",
    "neurologist": "95",
    "oncologue": "95",
    "oncologist": "95",
    "gastro-entérologue": "95",
    "gastroenterologist": "95",
    "pédiatre": "95",
    "pediatre": "95",
    "pediatrician": "95",
    "spécialiste": "95",
    "specialiste": "95",
    "specialist": "95",
    
    # Other healthcare professionals
    "sage-femme": "31",
    "sages-femmes": "31", 
    "midwife": "31",
    "dentiste": "86",
    "dentist": "86",
    "chirurgien-dentiste": "86",
    "pharmacien": "96",
    "pharmacist": "96",
    "kinésithérapeute": "80",
    "kinesitherapeute": "80",
    "psychologue": "101",
    "podologue": "90",
    "chiropracteur": "54",
}

def extract_role_from_query(query: str) -> str:
    """Extract healthcare professional role from natural language query"""
    query_lower = query.lower()
    print(f"[DEBUG] Extracting role from query: '{query}'")
    print(f"[DEBUG] Query lowercase: '{query_lower}'")
    
    # Look for role codes in the query
    for role_name, code in ROLE_CODES.items():
        if role_name in query_lower:
            print(f"[DEBUG] Found role '{role_name}' -> code '{code}'")
            return code
    
    # Default to general practitioners if no specific role found
    print(f"[DEBUG] No specific role found, defaulting to generaliste (60)")
    return "60"

def smart_search_strategy(query: str) -> dict:
    """Advanced search strategy with intelligent result limiting and context awareness"""
    import re
    
    query_lower = query.lower()
    
    # Analyze query intent for smart result limiting
    result_preference = analyze_query_intent(query_lower)
    search_params = {"_count": result_preference["count"]}
    search_strategy = "broad"
    
    # Extract practitioner name if mentioned (improved patterns)
    name_patterns = [
        r'(?:dr\.?|doctor|docteur)\s+([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]+)+)',  # Dr. First Last
        r'(?:info (?:on|about)|about)\s+([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]+\s+[A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]+)(?:\s|$)',  # info about First Last
        r'\b([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]{2,}\s+[A-ZÀ-Ÿ][a-zA-ZÀ-ÿ]{2,})\b(?=\s|$|,|\?)'  # Standalone proper names
    ]
    
    practitioner_name = None
    for pattern in name_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            name = matches[0].strip()
            # Filter out common words and professional terms that aren't names
            excluded_terms = [
                'please', 'info', 'information', 'find', 'get', 'some', 'nice', 'paris', 
                'dentist', 'dentiste', 'doctor', 'médecin', 'cardiologist', 'cardiologue',
                'specialist', 'spécialiste', 'pharmacien', 'pharmacist', 'generaliste',
                'généraliste', 'sage-femme', 'midwife', 'in paris', 'dentist in',
                'general practitioner', 'general', 'practitioner', 'healthcare provider',
                'health professional', 'medical doctor', 'the best', 'best', 'good',
                'top', 'recommend', 'near me', 'close to', 'around', 'area',
                'list all', 'all', 'list', 'many', 'several', 'multiple', 'compare',
                'options', 'choose', 'which', 'need a', 'find a'
            ]
            if (name.lower() not in excluded_terms and 
                len(name) > 4 and 
                not any(term in name.lower() for term in excluded_terms)):
                practitioner_name = name
                break
    
    # Extract geographic information for client-side filtering
    geographic_info = extract_geographic_context(query_lower)
    
    if practitioner_name:
        # Enhanced name-based search using proper FHIR parameters
        name_parts = practitioner_name.strip().split()
        if len(name_parts) >= 2:
            # Use family and given name parameters for better accuracy
            search_params["family"] = name_parts[-1]  # Last name is typically family name
            search_params["given"] = " ".join(name_parts[:-1])  # Everything else is given name
            search_strategy = "name_search"
            print(f"[DEBUG] Using FHIR name search: family={name_parts[-1]}, given={' '.join(name_parts[:-1])}")
        else:
            # Single name - try family name search
            search_params["family"] = practitioner_name
            search_strategy = "name_search"
            print(f"[DEBUG] Using family name search: {practitioner_name}")
    else:
        # Enhanced role-based search with better specialty detection
        role_code = detect_healthcare_role(query_lower)
        
        if role_code:
            search_params["role"] = role_code
            search_strategy = "role_search"
            print(f"[DEBUG] Using role search: {role_code}")
        else:
            print(f"[DEBUG] Using broad search - will let AI filter results")
    
    return {
        "params": search_params,
        "strategy": search_strategy,
        "detected_name": practitioner_name,
        "geographic_info": geographic_info,
        "result_preference": result_preference
    }

def analyze_query_intent(query_lower: str) -> dict:
    """Analyze query to determine appropriate result count and filtering preferences"""
    
    # Look for quantity indicators
    if any(word in query_lower for word in ['list', 'all', 'many', 'several', 'multiple']):
        return {"count": 50, "preference": "comprehensive", "limit_results": False}
    
    # Look for specific/targeted searches
    if any(word in query_lower for word in ['best', 'top', 'good', 'recommend', 'find a', 'need a']):
        return {"count": 20, "preference": "curated", "limit_results": True}
    
    # Look for comparison/research queries
    if any(word in query_lower for word in ['compare', 'options', 'choose', 'which']):
        return {"count": 30, "preference": "comparative", "limit_results": True}
    
    # Default for general queries
    return {"count": 25, "preference": "balanced", "limit_results": True}

def extract_geographic_context(query_lower: str) -> dict:
    """Extract geographic information for client-side filtering"""
    geographic_info = {"city": None, "district": None, "postal_code": None, "region": None}
    
    # Paris districts
    paris_patterns = [
        (r'paris\s+(\d{1,2})(?:e|è|ème|eme)?', 'district'),
        (r'(\d{1,2})(?:e|è|ème|eme)\s+arrondissement', 'district'),
        (r'(\d{5})', 'postal_code'),  # French postal codes
    ]
    
    # Major French cities
    cities = [
        'paris', 'marseille', 'lyon', 'toulouse', 'nice', 'nantes', 'montpellier',
        'strasbourg', 'bordeaux', 'lille', 'rennes', 'reims', 'saint-étienne',
        'toulon', 'grenoble', 'dijon', 'angers', 'nîmes', 'villeurbanne'
    ]
    
    for city in cities:
        if city in query_lower:
            geographic_info["city"] = city.capitalize()
            break
    
    for pattern, geo_type in paris_patterns:
        match = re.search(pattern, query_lower)
        if match:
            if geo_type == 'district':
                district_num = int(match.group(1))
                if 1 <= district_num <= 20:
                    geographic_info["district"] = f"Paris {district_num}"
                    geographic_info["city"] = "Paris"
                    geographic_info["postal_code"] = f"750{district_num:02d}"
            elif geo_type == 'postal_code':
                postal = match.group(1)
                if postal.startswith('75') and len(postal) == 5:
                    geographic_info["postal_code"] = postal
                    geographic_info["city"] = "Paris"
    
    return geographic_info

def detect_healthcare_role(query_lower: str) -> str:
    """Enhanced role detection with fuzzy matching and context awareness"""
    
    # Priority matching for most specific terms first
    priority_roles = [
        # Specific specialists
        ("cardiologue", "95"), ("cardiologist", "95"), ("cardiologie", "95"),
        ("dermatologue", "95"), ("dermatologist", "95"), ("dermatology", "95"),
        ("gynécologue", "95"), ("gynecologist", "95"), ("gynecology", "95"),
        ("pédiatre", "95"), ("pediatre", "95"), ("pediatrician", "95"),
        ("psychiatre", "95"), ("psychiatrist", "95"), ("psychiatry", "95"),
        ("ophtalmologue", "95"), ("ophthalmologist", "95"), ("eye doctor", "95"),
        ("neurologue", "95"), ("neurologist", "95"), ("neurology", "95"),
        ("urologue", "95"), ("urologist", "95"), ("urology", "95"),
        ("gastro-entérologue", "95"), ("gastroenterologist", "95"),
        ("oncologue", "95"), ("oncologist", "95"), ("cancer", "95"),
        ("radiologue", "95"), ("radiologist", "95"),
        
        # Other professionals
        ("sage-femme", "31"), ("midwife", "31"), ("sages-femmes", "31"),
        ("dentiste", "86"), ("dentist", "86"), ("chirurgien-dentiste", "86"),
        ("pharmacien", "96"), ("pharmacist", "96"), ("pharmacy", "96"),
        ("kinésithérapeute", "80"), ("physiotherapist", "80"), ("kiné", "80"),
        ("psychologue", "101"), ("psychologist", "101"),
        
        # General practitioners (lower priority to avoid over-matching)
        ("médecin généraliste", "60"), ("general practitioner", "60"),
        ("généraliste", "60"), ("generaliste", "60"), ("gp", "60"),
    ]
    
    # Find the longest matching term (more specific)
    best_match = None
    best_length = 0
    
    for term, code in priority_roles:
        if term in query_lower and len(term) > best_length:
            best_match = code
            best_length = len(term)
    
    return best_match

def make_direct_api_call(search_config: dict) -> dict:
    """Make direct API call to Annuaire Santé with smart search strategy"""
    url = f"https://gateway.api.esante.gouv.fr/fhir/PractitionerRole"
    headers = {
        "ESANTE-API-KEY": ANNUAIRE_SANTE_API_KEY,
        "Accept": "application/json"
    }
    
    params = search_config["params"]
    strategy = search_config["strategy"]
    
    # Detailed logging
    print(f"[DEBUG] Smart API Call:")
    print(f"[DEBUG] Strategy: {strategy}")
    print(f"[DEBUG] URL: {url}")
    print(f"[DEBUG] Params: {params}")
    print(f"[DEBUG] Full URL: {url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}")
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=20)
        print(f"[DEBUG] Response Status: {response.status_code}")
        response.raise_for_status()
        
        json_data = response.json()
        total_entries = len(json_data.get('entry', []))
        total_available = json_data.get('total', 'unknown')
        print(f"[DEBUG] API returned {total_entries} entries (total available: {total_available})")
        
        # Log some sample names to verify we're getting different data
        if json_data.get('entry'):
            sample_names = []
            for entry in json_data['entry'][:5]:
                name_ext = entry.get('resource', {}).get('extension', [])
                for ext in name_ext:
                    if 'PractitionerRole-Name' in ext.get('url', ''):
                        family = ext.get('valueHumanName', {}).get('family', '')
                        given = ext.get('valueHumanName', {}).get('given', [''])
                        full_name = f"{given[0] if given else ''} {family}".strip()
                        sample_names.append(full_name)
                        break
            print(f"[DEBUG] Sample names returned: {sample_names}")
        
        return json_data
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] API call failed: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        raise HTTPException(status_code=502, detail=f"API call failed: {str(e)}")

def ai_parse_fhir_data(query: str, fhir_data: dict, search_config: dict = None) -> dict:
    """Enhanced AI parsing with geographic filtering and smart result limiting"""
    
    # Create a more targeted prompt based on the data we have
    total_entries = len(fhir_data.get('entry', []))
    
    # Extract search context
    geographic_info = search_config.get('geographic_info', {}) if search_config else {}
    result_preference = search_config.get('result_preference', {}) if search_config else {}
    
    geographic_context = ""
    if geographic_info.get('city') or geographic_info.get('district') or geographic_info.get('postal_code'):
        geographic_context = f"""
GEOGRAPHIC FILTERING REQUESTED:
- City: {geographic_info.get('city', 'Not specified')}
- District: {geographic_info.get('district', 'Not specified')}
- Postal Code: {geographic_info.get('postal_code', 'Not specified')}

IMPORTANT: The API doesn't support geographic filtering, so you must filter results client-side by looking for address information in the FHIR data.
"""

    result_guidance = f"""
RESULT PREFERENCES:
- Query intent: {result_preference.get('preference', 'balanced')}
- Recommended result count: {result_preference.get('count', 25)}
- Should limit results: {result_preference.get('limit_results', True)}

RESULT SELECTION STRATEGY:
- If "curated" preference: Return only the most relevant/highest quality matches
- If "comprehensive" preference: Return more results but still prioritize quality
- If "comparative" preference: Return diverse options for comparison
- Always prioritize active practitioners with complete information
"""

    prompt = f"""
User Query: "{query}"

FHIR Data Analysis:
- Total practitioners retrieved: {total_entries}
- Data source: Annuaire Santé API (French healthcare directory)

{geographic_context}

{result_guidance}

Raw FHIR Data (first portion):
{json.dumps(fhir_data, indent=2)[:8000]}...

CRITICAL INSTRUCTIONS:
1. **GEOGRAPHIC FILTERING**: If location was specified, filter results by extracting address info from FHIR extensions
2. **SMART RESULT LIMITING**: Return only the most relevant results based on query intent
3. **NAME-BASED QUERIES**: If user asks for a specific practitioner name, PRIORITIZE exact name matches
4. **SPECIALTY FILTERING**: For specialty queries, look at profession codes AND organizational context
5. **NO FAKE DATA**: Only return practitioners that actually exist in the provided data
6. **QUALITY PRIORITIZATION**: Prioritize practitioners with complete information and active status

FHIR Data Structure Guide:
- Names: extension[].valueHumanName.family + given
- Addresses: Look for address extensions in extension[] arrays
- Profession codes: code[].coding[] with system "TRE_G15-ProfessionSante"
  - "60" = Médecin généraliste
  - "95" = Médecin spécialiste  
  - "31" = Sage-femme
  - "86" = Chirurgien-dentiste
  - "96" = Pharmacien
- Practice type: code[].coding[] with system "TRE_R23-ModeExercice"
  - "S" = Secteur libéral
  - "L" = Libéral
- Organization: organization.reference (if present)
- Active status: active field

RESPONSE FORMAT:
{{
  "message": "Natural, helpful response addressing user's specific query and location if specified",
  "natural_response": "Same as message",
  "structured_data": {{
    "success": true,
    "message": "Brief summary of search results with geographic context if applicable",
    "data": {{
      "results": [
        {{
          "name": "Full practitioner name",
          "title": "Professional title (Dr., etc.)",
          "specialty": "Professional role/specialty",
          "specialty_label": "Human readable specialty",
          "practice_type": "Practice setting",
          "fonction_label": "Professional function",
          "genre_activite_label": "Activity type",
          "organization_ref": "Organization reference or null",
          "active": true/false,
          "id": "PractitionerRole ID",
          "relevance_score": "1-10 score for query match",
          "match_reason": "Explanation of why this matches the query",
          "location": "Extracted location info if available"
        }}
      ],
      "search_analysis": {{
        "total_in_dataset": {total_entries},
        "matching_practitioners": "number that match criteria",
        "geographic_filtering_applied": "true/false",
        "result_limiting_applied": "true/false",
        "search_limitations": "explanation of API limitations",
        "user_query_type": "name_search/specialty_search/geographic_search/broad_search"
      }}
    }}
  }},
  "success": true
}}

IMPORTANT: Be honest about limitations and explain geographic filtering when location was specified.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert healthcare search assistant with deep knowledge of French healthcare system and FHIR data structures. You provide accurate, helpful responses and are transparent about system limitations."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.2  # Lower temperature for more consistent results
        )
        
        # Parse AI response as JSON
        ai_response = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        
        return json.loads(ai_response)
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] AI response not valid JSON: {e}")
        print(f"[DEBUG] AI response preview: {ai_response[:500]}...")
        # Enhanced fallback response
        return {
            "message": f"I retrieved {total_entries} practitioners from the database, but encountered a technical issue parsing the detailed information for your query: {query}. Please try rephrasing your request.",
            "natural_response": f"I retrieved {total_entries} practitioners from the database, but encountered a technical issue parsing the detailed information for your query: {query}. Please try rephrasing your request.",
            "structured_data": {
                "success": False,
                "message": "Technical parsing error occurred",
                "data": {
                    "results": [],
                    "search_analysis": {
                        "total_in_dataset": total_entries,
                        "matching_practitioners": 0,
                        "search_limitations": "JSON parsing error occurred",
                        "user_query_type": "unknown"
                    }
                }
            },
            "success": False
        }
    except Exception as e:
        print(f"[ERROR] AI parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {str(e)}")

@app.post("/mcp/execute")
async def mcp_execute(request: Request):
    """AI-Powered Smart MCP execution with intelligent query interpretation"""
    body = await request.json()
    query = body.get("prompt") or body.get("query") or ""

    try:
        print(f"[DEBUG] Processing query with AI: {query}")
        
        # Import the smart orchestrator
        from core_orchestration.smart_orchestrator import SmartHealthcareOrchestrator
        
        # Use AI-powered orchestration
        orchestrator = SmartHealthcareOrchestrator()
        result = orchestrator.process_query(query)
        
        if result.get("success"):
            print(f"[DEBUG] Detected organization query, routing to OrganizationMCP")
            # Route to organization search
            org_mcp = orchestrator.mcp_registry.get_mcp("organization")
            org_result = org_mcp.process_query(query)
            
            if org_result.get("success"):
                # Format organization results for consistent response structure
                organizations = org_result.get("results", [])
                response = {
                    "choices": [
                        {
                            "message": {
                                "content": f"I found {len(organizations)} healthcare organizations matching your criteria."
                            },
                            "data": {
                                "natural_response": f"I found {len(organizations)} healthcare organizations matching your criteria.",
                                "structured_data": {
                                    "success": True,
                                    "message": f"Found {len(organizations)} organizations",
                                    "data": {
                                        "results": organizations,
                                        "query_type": "organization_search",
                                        "search_metadata": {
                                            "query_type": "organization",
                                            "total_results": len(organizations)
                                        }
                                    }
                                },
                                "success": True
                            }
                        }
                    ]
                }
                return response
            else:
                # Organization search failed, return error
                return {
                    "choices": [
                        {
                            "message": {
                                "content": org_result.get("error", "No organizations found matching your criteria.")
                            },
                            "data": {
                                "natural_response": org_result.get("error", "No organizations found matching your criteria."),
                                "structured_data": {
                                    "success": False,
                                    "message": org_result.get("error", "No organizations found"),
                                    "data": {"results": []}
                                },
                                "success": False
                            }
                        }
                    ]
                }
        else:
            print(f"[DEBUG] Detected practitioner query, using existing logic")
            # Existing practitioner search logic
            # Determine smart search strategy
            search_config = smart_search_strategy(query)
            print(f"[DEBUG] Search strategy: {search_config['strategy']}")
            
            # Make API call with smart strategy
            fhir_data = make_direct_api_call(search_config)
            total_entries = len(fhir_data.get('entry', []))
            print(f"[DEBUG] Retrieved {total_entries} entries for processing")
            
            # Let AI intelligently parse and filter with search context
            result = ai_parse_fhir_data(query, fhir_data, search_config)
            
            # Update search parameters based on the enhanced strategy
            if result.get('structured_data', {}).get('data'):
                result['structured_data']['data']['search_metadata'] = {
                    "strategy_used": search_config['strategy'],
                    "detected_name": search_config.get('detected_name'),
                    "geographic_info": search_config.get('geographic_info', {}),
                    "result_preference": search_config.get('result_preference', {}),
                    "api_params": search_config['params'],
                    "total_retrieved": total_entries
                }
            
            # Log AI analysis results
            if result.get('structured_data', {}).get('data', {}).get('query_analysis'):
                analysis = result['structured_data']['data']['query_analysis']
                print(f"[DEBUG] AI Analysis: {analysis}")
            
            # Convert to MCP response format
            response = {
                "choices": [
                    {
                        "message": {
                            "content": result.get("message", "Query processed successfully")
                        },
                        "data": {
                            "natural_response": result.get("natural_response"),
                            "structured_data": result.get("structured_data", {}),
                            "success": result.get("success", False)
                        }
                    }
                ]
            }
            
            return response

    except Exception as e:
        print(f"[ERROR] Query processing failed: {e}")
        return {
            "choices": [
                {
                    "message": {
                        "content": f"I'm sorry, I encountered an error while processing your request: {str(e)}"
                    },
                    "data": {
                        "natural_response": f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                        "structured_data": {
                            "success": False,
                            "message": f"Error: {str(e)}",
                            "data": {"results": []}
                        },
                        "success": False
                    }
                }
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
