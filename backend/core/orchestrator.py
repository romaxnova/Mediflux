from typing import Dict, List, Any
import openai
import os
from dotenv import load_dotenv
from .base_mcp import BaseMCP, MCPRegistry
from .intent_parser import IntentParser

# Load environment variables
load_dotenv()

class HealthcareOrchestrator:
    def __init__(self):
        self.mcp_registry = MCPRegistry()
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def register_mcp(self, name: str, mcp: BaseMCP):
        """Register a new MCP with the orchestrator"""
        self.mcp_registry.register(name, mcp)

    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict:
        """Simplified query processing that directly calls appropriate MCP"""
        try:
            # Parse intent and entities
            intent = IntentParser.parse(query)
            
            print(f"[DEBUG] Parsed intent: {intent}")  # Debug log

            # Simple routing based on intent type
            if intent["type"] == "find_organization":
                org_mcp = self.mcp_registry.get_mcp("organization")
                if org_mcp:
                    result = org_mcp.process_query(query, context)
                    # Generate natural language response
                    natural_response = self.generate_natural_response(query, result)
                    return {
                        "message": natural_response,
                        "natural_response": natural_response,
                        "structured_data": result,
                        "success": True
                    }
            
            elif intent["type"] == "find_practitioner":
                prac_mcp = self.mcp_registry.get_mcp("practitioner")
                if prac_mcp:
                    result = prac_mcp.process_query(query, context)
                    # Generate natural language response
                    natural_response = self.generate_natural_response(query, result)
                    return {
                        "message": natural_response,
                        "natural_response": natural_response,
                        "structured_data": result,
                        "success": True
                    }
            
            # Fallback for unrecognized queries
            fallback_result = {"message": "Could not understand query type", "data": intent, "success": False}
            natural_response = self.generate_natural_response(query, fallback_result)
            return {
                "message": natural_response,
                "natural_response": natural_response,
                "structured_data": fallback_result,
                "success": False
            }
            
        except Exception as e:
            print(f"[ERROR] Orchestrator error: {e}")
            error_result = {"message": f"Error processing query: {str(e)}", "data": {}, "success": False}
            natural_response = f"I'm sorry, I encountered an error while processing your request: {str(e)}"
            return {
                "message": natural_response,
                "natural_response": natural_response,
                "structured_data": error_result,
                "success": False
            }

    def generate_natural_response(self, query: str, structured_data: Dict[str, Any]) -> str:
        """Convert structured API response to natural language using OpenAI"""
        try:
            # Extract key information from structured data
            success = structured_data.get("success", False)
            message = structured_data.get("message", "")
            data = structured_data.get("data", {})
            
            if not success:
                return f"I'm sorry, I couldn't find what you're looking for. {message}"
            
            # Handle practitioner results
            if "results" in data:
                results = data["results"]
                if not results:
                    return "I couldn't find any healthcare professionals matching your criteria. You might want to try expanding your search area or checking different specialties."
                
                # Create a prompt for OpenAI
                prompt = f"""
Transform this healthcare search result into a natural, conversational response to the user's query: "{query}"

Search Results:
{results}

Requirements:
- Be conversational and helpful
- Include the practitioner names and specialties
- Mention the location if relevant
- Keep it concise but informative
- Sound natural, not robotic
- Use "I found" instead of "The system found"
"""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful healthcare assistant that provides clear, conversational responses about healthcare providers."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                return response.choices[0].message.content.strip()
            
            # Fallback for other types of responses
            return message
            
        except Exception as e:
            print(f"[ERROR] OpenAI API error: {e}")
            # Fallback to structured response
            if "results" in structured_data.get("data", {}):
                results = structured_data["data"]["results"]
                if results:
                    names = [r.get("name", "Unknown") for r in results[:3]]
                    return f"I found {len(results)} healthcare professionals: {', '.join(names)}{'...' if len(results) > 3 else ''}."
            return structured_data.get("message", "I found some results for you.")
