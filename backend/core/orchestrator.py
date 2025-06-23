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

    def ai_interpret_query(self, query: str) -> Dict[str, Any]:
        """Use AI to interpret the query with healthcare context"""
        try:
            prompt = f"""
Analyze this healthcare query and provide structured interpretation:

Query: "{query}"

You are an AI assistant that interprets healthcare search queries in French and English. 
Analyze the query and return a JSON object with this structure:

{{
    "intent": "practitioner" or "organization",
    "confidence": 0.0-1.0,
    "extracted_entities": {{
        "specialty": "medical specialty if mentioned",
        "entity_type": ["hospital", "pharmacy", "clinic", etc.],
        "location": {{
            "city": "city name",
            "postal_code": "postal code if mentioned",
            "arrondissement": "Paris arrondissement if mentioned"
        }},
        "practitioner_name": "specific name if mentioned",
        "organization_name": "specific name if mentioned"
    }},
    "search_strategy": {{
        "primary": "practitioner" or "organization",
        "fallback": null or "practitioner"/"organization"
    }},
    "reasoning": "Brief explanation of interpretation"
}}

Examples:
- "je cherche un cardiologue" -> practitioner intent
- "find hospitals" -> organization intent
- "pharmacie à Paris" -> organization intent
- "Dr. Smith" -> practitioner intent

Rules:
- Queries about specific medical specialties (cardiologue, dentiste, etc.) = practitioner
- Queries about facilities (hôpital, pharmacie, clinique, etc.) = organization
- Convert Paris arrondissements (16e -> 75016)
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            ai_result = json.loads(response.choices[0].message.content)
            print(f"[DEBUG] AI interpretation: {ai_result}")
            return ai_result
            
        except Exception as e:
            print(f"[ERROR] AI interpretation failed: {e}")
            # Fallback to original intent parser
            return IntentParser.parse(query)

    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict:
        """Enhanced query processing with AI interpretation"""
        try:
            # Use AI interpretation first, fallback to original parser
            try:
                intent = self.ai_interpret_query(query)
                print(f"[DEBUG] AI interpreted intent: {intent}")
            except:
                intent = IntentParser.parse(query)
                print(f"[DEBUG] Fallback to original intent: {intent}")
            
            # Route based on AI interpretation
            if intent.get("intent") == "practitioner" or intent.get("type") == "find_practitioner":
                prac_mcp = self.mcp_registry.get_mcp("practitioner")
                if prac_mcp:
                    result = prac_mcp.process_query(query, context)
                    natural_response = self.generate_natural_response(query, result)
                    return {
                        "message": natural_response,
                        "natural_response": natural_response,
                        "structured_data": result,
                        "success": True,
                        "ai_interpretation": intent
                    }
            
            elif intent.get("intent") == "organization" or intent.get("type") == "find_organization":
                org_mcp = self.mcp_registry.get_mcp("organization")
                if org_mcp:
                    result = org_mcp.process_query(query, context)
                    natural_response = self.generate_natural_response(query, result)
                    return {
                        "message": natural_response,
                        "natural_response": natural_response,
                        "structured_data": result,
                        "success": True,
                        "ai_interpretation": intent
                    }
            
            # Fallback for unrecognized queries - try organization first
            print(f"[DEBUG] Fallback routing for query: {query}")
            org_mcp = self.mcp_registry.get_mcp("organization")
            if org_mcp:
                result = org_mcp.process_query(query, context)
                if result.get("success") and result.get("data", {}).get("results"):
                    natural_response = self.generate_natural_response(query, result)
                    return {
                        "message": natural_response,
                        "natural_response": natural_response,
                        "structured_data": result,
                        "success": True,
                        "ai_interpretation": intent
                    }
            
            # Final fallback
            fallback_result = {"message": "Could not understand query type", "data": intent, "success": False}
            natural_response = self.generate_natural_response(query, fallback_result)
            return {
                "message": natural_response,
                "natural_response": natural_response,
                "structured_data": fallback_result,
                "success": False,
                "ai_interpretation": intent
            }

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
                
                # Create a prompt for OpenAI to generate a rich, informative response
                prompt = f"""
Transform this healthcare search result into a natural, informative response to the user's query: "{query}"

Search Results:
{results}

Available data fields per practitioner:
- name, title, specialty_label 
- practice_type (e.g., "Secteur libéral")
- fonction_label (e.g., "Exercice régulier", "Chef de service")
- genre_activite_label (e.g., "Activité principale")
- organization_ref (hospital/clinic affiliation if present)
- smart_card info (professional credentials)
- active status

Requirements:
- Be conversational and helpful
- Include practitioner names and specialties clearly
- Mention practice setting (secteur libéral, établissement, etc.) to help users understand the context
- Include professional status (exercice régulier, chef de service, etc.) when relevant
- If organization_ref exists, mention institutional affiliation
- Keep it informative but concise (2-3 sentences per practitioner)
- Sound natural and professional, like a knowledgeable healthcare assistant
- Use "I found" instead of "The system found"
- For multiple practitioners, clearly separate each one
- Focus on practical information users need to make healthcare decisions

Example style: "I found 2 sage-femmes in the 17th arrondissement. Dr. Dorina Ernst practices in the liberal sector with regular exercise status. Justine Ayello is also in liberal practice and has an institutional affiliation."
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
            # Fallback to structured response with enhanced formatting
            if "results" in structured_data.get("data", {}):
                results = structured_data["data"]["results"]
                if results:
                    # Create a more informative fallback response
                    practitioner_summaries = []
                    for r in results[:3]:
                        name = r.get("name", "Unknown")
                        specialty = r.get("specialty_label") or r.get("specialty", "Unknown")
                        title = r.get("title", "")
                        practice_type = r.get("practice_type", "")
                        
                        summary = f"{name}"
                        if title:
                            summary += f" ({title})"
                        summary += f" - {specialty}"
                        if practice_type and practice_type != "Cabinet privé":
                            summary += f" [{practice_type}]"
                        
                        practitioner_summaries.append(summary)
                    
                    more_text = f" and {len(results) - 3} more" if len(results) > 3 else ""
                    return f"I found {len(results)} healthcare professionals: {'; '.join(practitioner_summaries)}{more_text}."
            return structured_data.get("message", "I found some results for you.")
