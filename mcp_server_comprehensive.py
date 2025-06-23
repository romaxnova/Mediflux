#!/usr/bin/env python3
# filepath: /Users/romanstadnikov/Library/OpenManus/workspace/mediflux/mcp_server_comprehensive.py
"""
Comprehensive MCP Server for Healthcare Search
Leverages all 5 FHIR resources with intelligent AI-powered orchestration
"""

import json
import os
import sys
from typing import Dict, Any, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add the core_orchestration directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core_orchestration'))

from core_orchestration.comprehensive_orchestrator import ComprehensiveHealthcareOrchestrator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Comprehensive Healthcare MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7000", "http://127.0.0.1:7000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the comprehensive orchestrator
orchestrator = ComprehensiveHealthcareOrchestrator()

class QueryRequest(BaseModel):
    query: str
    prompt: str = ""

@app.post("/mcp/execute")
async def mcp_execute(request: Request):
    """
    Main MCP execution endpoint using comprehensive FHIR orchestration
    Handles all types of healthcare queries intelligently
    """
    try:
        body = await request.json()
        
        # Extract query from various possible fields
        query = (
            body.get("query") or 
            body.get("prompt") or 
            body.get("message") or 
            ""
        )
        
        if not query.strip():
            return {
                "choices": [{
                    "message": {
                        "content": "Veuillez fournir une requête de recherche."
                    },
                    "data": {
                        "success": False,
                        "message": "Requête vide",
                        "results": []
                    }
                }]
            }
        
        print(f"[COMPREHENSIVE_MCP] Processing query: {query}")
        
        # Process query using comprehensive orchestrator
        result = orchestrator.process_query(query)
        
        # Format response for MCP protocol
        if result.get("success"):
            message_content = result.get("message", f"Trouvé {result.get('count', 0)} résultats")
            
            # Create natural language response based on results
            results = result.get("results", [])
            if results:
                resource_types = {}
                for r in results:
                    rtype = r.get("resource_type", "unknown")
                    resource_types[rtype] = resource_types.get(rtype, 0) + 1
                
                # Create detailed message
                type_descriptions = {
                    "organization": "organisations de santé",
                    "practitioner": "professionnels de santé", 
                    "healthcare_service": "services de santé",
                    "device": "équipements médicaux"
                }
                
                summary_parts = []
                for rtype, count in resource_types.items():
                    desc = type_descriptions.get(rtype, rtype)
                    summary_parts.append(f"{count} {desc}")
                
                detailed_message = f"J'ai trouvé {', '.join(summary_parts)} correspondant à votre recherche."
                
                # Add examples of what was found
                examples = []
                for i, r in enumerate(results[:3]):  # Show first 3 examples
                    if r.get("resource_type") == "organization":
                        examples.append(f"• {r.get('name', 'Organisation')} ({r.get('type', 'Type inconnu')})")
                    elif r.get("resource_type") == "practitioner":
                        examples.append(f"• {r.get('name', 'Professionnel')} - {r.get('specialty', 'Spécialité')}")
                    elif r.get("resource_type") == "healthcare_service":
                        examples.append(f"• {r.get('name', 'Service')} - {r.get('category', 'Catégorie')}")
                    elif r.get("resource_type") == "device":
                        examples.append(f"• {r.get('name', 'Équipement')} ({r.get('type', 'Type')})")
                
                if examples:
                    detailed_message += f"\n\nExemples:\n" + "\n".join(examples)
                
                if len(results) > 3:
                    detailed_message += f"\n\n... et {len(results) - 3} autres résultats."
                
                message_content = detailed_message
        else:
            message_content = f"Désolé, je n'ai pas pu trouver de résultats pour votre recherche: {query}"
            if result.get("error"):
                message_content += f"\nErreur: {result['error']}"
        
        response = {
            "choices": [{
                "message": {
                    "content": message_content
                },
                "data": {
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "results": result.get("results", []),
                    "count": result.get("count", 0),
                    "search_type": result.get("search_type", "unknown"),
                    "ai_interpretation": result.get("ai_interpretation", {}),
                    "error": result.get("error")
                }
            }]
        }
        
        print(f"[COMPREHENSIVE_MCP] Response: {result.get('success')} - {result.get('count', 0)} results")
        return response
        
    except Exception as e:
        print(f"[COMPREHENSIVE_MCP_ERROR] Request processing failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "choices": [{
                "message": {
                    "content": f"Je suis désolé, une erreur s'est produite lors du traitement de votre demande: {str(e)}"
                },
                "data": {
                    "success": False,
                    "message": f"Erreur: {str(e)}",
                    "results": [],
                    "error": str(e)
                }
            }]
        }

@app.get("/health")
def health_check():
    """Health check endpoint with comprehensive system status"""
    api_key_configured = bool(os.getenv("ANNUAIRE_SANTE_API_KEY"))
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    
    status = "healthy" if (api_key_configured and openai_configured) else "degraded"
    
    return {
        "status": status,
        "service": "Comprehensive Healthcare MCP Server",
        "version": "2.0",
        "capabilities": [
            "Organization search (hospitals, clinics, pharmacies)",
            "PractitionerRole search (professionals by specialty)",
            "Practitioner search (professionals by name)", 
            "HealthcareService search (medical services)",
            "Device search (medical equipment)",
            "AI-powered query interpretation",
            "Multi-resource parallel search",
            "French language support",
            "Geographic filtering"
        ],
        "api_configured": api_key_configured,
        "openai_configured": openai_configured,
        "fhir_resources": 5,
        "endpoints": {
            "main": "/mcp/execute",
            "health": "/health"
        }
    }

@app.get("/capabilities")
def get_capabilities():
    """Return detailed capabilities of the comprehensive MCP server"""
    return {
        "fhir_resources": {
            "Organization": {
                "description": "Healthcare organizations (hospitals, clinics, pharmacies)",
                "search_parameters": ["name", "address-city", "address-postalcode", "type", "active"],
                "use_cases": ["Find hospitals in a city", "Locate pharmacies", "Search medical centers"]
            },
            "PractitionerRole": {
                "description": "Healthcare professionals in their professional context",
                "search_parameters": ["role", "organization", "location", "active"],
                "use_cases": ["Find specialists by profession", "Locate general practitioners", "Search by medical specialty"]
            },
            "Practitioner": {
                "description": "Individual healthcare professionals searchable by name",
                "search_parameters": ["name", "family", "given", "identifier"],
                "use_cases": ["Find doctor by name", "Search specific practitioner", "Lookup by RPPS number"]
            },
            "HealthcareService": {
                "description": "Specific medical services offered by organizations",
                "search_parameters": ["service-category", "service-type", "organization"],
                "use_cases": ["Find emergency services", "Locate radiology services", "Search laboratory services"]
            },
            "Device": {
                "description": "Medical devices and equipment",
                "search_parameters": ["type", "organization", "status"],
                "use_cases": ["Find MRI machines", "Locate CT scanners", "Search medical equipment"]
            }
        },
        "ai_capabilities": {
            "query_interpretation": "Intelligent parsing of natural language queries in French and English",
            "resource_routing": "Automatic determination of which FHIR resources to search",
            "parallel_search": "Ability to search multiple resources simultaneously",
            "fallback_strategies": "Intelligent fallbacks when primary searches fail",
            "geographic_processing": "Conversion of locations to proper FHIR parameters"
        },
        "supported_languages": ["French", "English"],
        "supported_locations": "France (all cities and postal codes, including Paris arrondissements)"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    port = int(os.getenv("MCP_PORT", "9002"))
    
    print("=" * 60)
    print("🏥 COMPREHENSIVE HEALTHCARE MCP SERVER")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"FHIR API Key: {'✓ Configured' if os.getenv('ANNUAIRE_SANTE_API_KEY') else '✗ Missing'}")
    print(f"OpenAI API Key: {'✓ Configured' if os.getenv('OPENAI_API_KEY') else '✗ Missing'}")
    print("Supported Resources:")
    print("  • Organization (hospitals, clinics, pharmacies)")
    print("  • PractitionerRole (professionals by specialty)")
    print("  • Practitioner (professionals by name)")
    print("  • HealthcareService (medical services)")
    print("  • Device (medical equipment)")
    print("Features:")
    print("  • AI-powered query interpretation")
    print("  • Multi-resource search orchestration")
    print("  • French/English language support")
    print("  • Geographic intelligence")
    print("  • Parallel search capabilities")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=port)
