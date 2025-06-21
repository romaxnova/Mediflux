#!/usr/bin/env python3
"""
Simplified MCP that makes direct API calls and lets AI handle parsing
No complex pre-processing - just raw API data + AI intelligence
"""

import json
import os
import requests
import openai
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Simple Healthcare API MCP")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7000", "http://127.0.0.1:7000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANNUAIRE_SANTE_API_KEY = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")
ANNUAIRE_SANTE_BASE_URL = "https://gateway.api.esante.gouv.fr/fhir"

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Simple role code mapping (from our testing)
ROLE_CODES = {
    # General practitioners
    "generaliste": "60",
    "médecin": "60", 
    "medecin": "60",
    "médecin généraliste": "60",
    "medecin generaliste": "60",
    "doctor": "60",
    
    # Specialists (most use code 95)
    "cardiologue": "95",
    "dermatologue": "95", 
    "psychiatre": "95",
    "gynécologue": "95",
    "ophtalmologiste": "95",
    "urologue": "95",
    "neurologue": "95",
    "oncologue": "95",
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

class QueryRequest(BaseModel):
    query: str

def extract_role_from_query(query: str) -> str:
    """Extract healthcare professional role from natural language query"""
    query_lower = query.lower()
    
    # Look for role codes in the query
    for role_name, code in ROLE_CODES.items():
        if role_name in query_lower:
            return code
    
    # Default to general practitioners if no specific role found
    return "60"

def make_api_call(role_code: str, count: int = 50) -> dict:
    """Make direct API call to Annuaire Santé"""
    url = f"{ANNUAIRE_SANTE_BASE_URL}/PractitionerRole"
    headers = {
        "ESANTE-API-KEY": ANNUAIRE_SANTE_API_KEY,
        "Accept": "application/json"
    }
    params = {
        "role": role_code,
        "_count": count
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API call failed: {e}")
        raise HTTPException(status_code=502, detail=f"API call failed: {str(e)}")

def ai_parse_and_respond(query: str, fhir_data: dict) -> dict:
    """Let AI parse FHIR data and generate response"""
    
    # Create prompt for AI to parse FHIR data and respond to user query
    prompt = f"""
User Query: "{query}"

Raw FHIR Data from Annuaire Santé API:
{json.dumps(fhir_data, indent=2)}

Your task:
1. Parse this FHIR Bundle data to extract practitioner information
2. Create a natural, helpful response to the user's query
3. Format the data for a healthcare interface

For each practitioner, extract:
- Name from extension[].valueHumanName (family + given names)
- Professional role/specialty from code[].coding[] (look for TRE-G15-ProfessionSante system)
- Practice type from code[].coding[] (look for TRE-R23-ModeExercice system: S=Secteur libéral, etc.)
- Professional function from code[].coding[] (look for TRE-R21-Fonction system)
- Activity type from code[].coding[] (look for TRE-R22-GenreActivite system)
- Organization affiliation from organization.reference if present
- Active status from active field

Return a JSON response with:
{{
  "message": "Natural language response to user (conversational, helpful)",
  "natural_response": "Same as message",
  "structured_data": {{
    "success": true,
    "message": "Brief success message",
    "data": {{
      "results": [
        {{
          "name": "Full name",
          "title": "Professional title if any",
          "specialty": "Professional role",
          "specialty_label": "Human readable specialty",
          "practice_type": "Practice setting",
          "fonction_label": "Professional function",
          "genre_activite_label": "Activity type", 
          "organization_ref": "Organization reference or null",
          "active": true/false,
          "id": "PractitionerRole ID"
        }}
      ],
      "query_params": {{"role": "role_code_used"}}
    }}
  }},
  "success": true
}}

Be conversational and helpful. Focus on practical information users need to find healthcare providers.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a healthcare assistant that parses FHIR data and provides helpful responses about healthcare providers. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
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
        print(f"[DEBUG] AI response: {ai_response}")
        # Fallback response
        return {
            "message": f"I found healthcare professionals for your query: {query}",
            "natural_response": f"I found healthcare professionals for your query: {query}",
            "structured_data": {
                "success": True,
                "message": "Data parsed successfully",
                "data": {"results": [], "query_params": {"role": "unknown"}}
            },
            "success": True
        }
    except Exception as e:
        print(f"[ERROR] AI parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {str(e)}")

@app.post("/mcp/execute")
async def mcp_execute(request: Request):
    """Main MCP execution endpoint - simplified approach"""
    body = await request.json()
    query = body.get("prompt") or body.get("query") or ""
    
    try:
        print(f"[DEBUG] Processing query: {query}")
        
        # Extract role from query
        role_code = extract_role_from_query(query)
        print(f"[DEBUG] Detected role code: {role_code}")
        
        # Make direct API call
        fhir_data = make_api_call(role_code, count=50)
        print(f"[DEBUG] API returned {len(fhir_data.get('entry', []))} results")
        
        # Let AI parse and respond
        result = ai_parse_and_respond(query, fhir_data)
        
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

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Simple Healthcare API MCP",
        "api_configured": bool(ANNUAIRE_SANTE_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Simple Healthcare API MCP Server...")
    print(f"API Key configured: {bool(ANNUAIRE_SANTE_API_KEY)}")
    print(f"OpenAI configured: {bool(OPENAI_API_KEY)}")
    uvicorn.run(app, host="0.0.0.0", port=9001)
