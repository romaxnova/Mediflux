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
    org_mcp = orchestrator.mcp_registry.get_mcp("organization")
    return {"result": org_mcp.process_query(req.query)}

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
    """MCP execution endpoint that handles both organization and practitioner queries"""
    body = await request.json()
    prompt = body.get("prompt") or body.get("query") or ""

    try:
        # Route query through the orchestrator
        result = orchestrator.process_query(prompt)

        # Convert orchestrator result to MCP response format
        response = {
            "choices": [
                {
                    "message": {
                        "content": result.get("message", "Query processed successfully")
                    },
                    "data": result.get("data", {})
                }
            ]
        }
        return response

    except Exception as e:
        return {
            "error": f"Query processing failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
