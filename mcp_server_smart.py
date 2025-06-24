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

# Load API configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
ANNUAIRE_SANTE_API_KEY = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")

# Initialize XAI (Grok) client
openai_client = openai.OpenAI(
    api_key=XAI_API_KEY, 
    base_url="https://api.x.ai/v1"
)

class QueryRequest(BaseModel):
    query: str

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
            # Format results for consistent response structure
            results = result.get("results", [])
            search_type = result.get("search_type", "unknown")
            ai_interpretation = result.get("ai_interpretation", {})
            
            response = {
                "choices": [
                    {
                        "message": {
                            "content": result.get("message", f"I found {len(results)} healthcare resources matching your criteria.")
                        },
                        "data": {
                            "natural_response": result.get("message", f"I found {len(results)} healthcare resources matching your criteria."),
                            "structured_data": {
                                "success": True,
                                "message": result.get("message", f"Found {len(results)} resources"),
                                "data": {
                                    "results": results,
                                    "query_type": search_type,
                                    "search_metadata": {
                                        "ai_interpretation": ai_interpretation,
                                        "total_results": len(results),
                                        "search_strategy": ai_interpretation.get("search_strategy", {}),
                                        "confidence": ai_interpretation.get("confidence", 0.0)
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
            # Search failed, return error
            return {
                "choices": [
                    {
                        "message": {
                            "content": result.get("error", "No results found matching your criteria.")
                        },
                        "data": {
                            "natural_response": result.get("error", "No results found matching your criteria."),
                            "structured_data": {
                                "success": False,
                                "message": result.get("error", "No results found"),
                                "data": {"results": []}
                            },
                            "success": False
                        }
                    }
                ]
            }

    except Exception as e:
        print(f"[ERROR] Smart MCP execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "choices": [
                {
                    "message": {
                        "content": f"Sorry, I encountered an error while processing your request: {str(e)}"
                    },
                    "data": {
                        "natural_response": f"Error: {str(e)}",
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
    uvicorn.run(app, host="0.0.0.0", port=9000)
