import requests
import re
import os
from typing import Dict, Any
import sys
try:
    from backend.core.base_mcp import BaseMCP
except ImportError as e:
    raise ImportError("Could not import BaseMCP. Make sure to run this script from the 'workspace/mediflux' directory or set PYTHONPATH accordingly.\nOriginal error: {}".format(e))

# Paris arrondissement to postal code mapping (partial, can be extended)
PARIS_ARR_MAP = {
    "1er": "75001", "2e": "75002", "3e": "75003", "4e": "75004", "5e": "75005", "6e": "75006", "7e": "75007", "8e": "75008", "9e": "75009",
    "10e": "75010", "11e": "75011", "12e": "75012", "13e": "75013", "14e": "75014", "15e": "75015", "16e": "75016", "17e": "75017", "18e": "75018", "19e": "75019", "20e": "75020",
    "1st": "75001", "2nd": "75002", "3rd": "75003", "4th": "75004", "5th": "75005", "6th": "75006", "7th": "75007", "8th": "75008", "9th": "75009",
    "10th": "75010", "11th": "75011", "12th": "75012", "13th": "75013", "14th": "75014", "15th": "75015", "16th": "75016", "17th": "75017", "18th": "75018", "19th": "75019", "20th": "75020",
    "premier": "75001", "deuxième": "75002", "troisième": "75003", "quatrième": "75004", "cinquième": "75005", "sixième": "75006", "septième": "75007", "huitième": "75008", "neuvième": "75009",
    "dixième": "75010", "onzième": "75011", "douzième": "75012", "treizième": "75013", "quatorzième": "75014", "quinzième": "75015", "seizième": "75016", "dix-septième": "75017", "dix-huitième": "75018", "dix-neuvième": "75019", "vingtième": "75020"
}

def arrondissement_to_postal(query: str):
    m = re.search(r"paris[\s-]*(\d{1,2})(?:er|e|ème|th|st|nd|rd)?", query, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 20:
            return f"750{num:02d}"
    for k, v in PARIS_ARR_MAP.items():
        if k in query.lower():
            return v
    return None

def parse_organization_query(query: str):
    """
    Parse a natural language query for FHIR Organization search.
    Supports FHIR parameters: _id, identifier, active, name, type, address, address-city, address-postalcode, _lastUpdated, and modifiers.
    Returns: count, params (dict of FHIR search parameters)
    """
    count = 3
    params = {}
    
    # Extract count first
    count_match = re.search(r'(?:find|show|get|list)\s+(\d+)', query, re.IGNORECASE)
    if count_match:
        count = int(count_match.group(1))
    
    # Extract postal code (5 digits)
    postal_match = re.search(r'\b(\d{5})\b', query)
    if postal_match:
        params["address-postalcode"] = postal_match.group(1)
        # Remove postal code from query for name extraction
        query = re.sub(r'\b\d{5}\b', '', query).strip()
    
    # Check for Paris arrondissement if no postal code found
    if "address-postalcode" not in params:
        postal_code = arrondissement_to_postal(query)
        if postal_code:
            params["address-postalcode"] = postal_code
    
    # Extract organization name/type (after removing action words and postal codes)
    # Remove common action words and prepositions
    clean_query = re.sub(r'\b(?:find|show|get|list|in|from|at|near|of|the|a|an)\b', '', query, flags=re.IGNORECASE)
    clean_query = re.sub(r'\b\d+\b', '', clean_query)  # Remove any remaining numbers
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()  # Clean up whitespace
    
    if clean_query:
        params["name"] = clean_query
    
    # Address/city extraction
    city_match = re.search(r'\bin\s+([a-zA-Z\s\-\']+)(?:\s+\d{5})?$', query, re.IGNORECASE)
    if city_match and not postal_match:  # Only if we don't already have postal code
        city = city_match.group(1).strip()
        if city.lower() != 'paris':  # Don't add generic "Paris" as city filter
            params["address-city"] = city
    
    # FHIR modifiers (e.g. name:exact, identifier:contains)
    modifier_matches = re.findall(r'(\w+):(exact|contains|missing|text)\s+([^\s]+)', query)
    for field, modifier, value in modifier_matches:
        params[f"{field}:{modifier}"] = value
    
    # FHIR specific parameters
    id_match = re.search(r'id[:=]\s*([\w-]+)', query)
    if id_match:
        params["_id"] = id_match.group(1)
    
    identifier_match = re.search(r'identifier[:=]\s*([\w-]+)', query)
    if identifier_match:
        params["identifier"] = identifier_match.group(1)
    
    active_match = re.search(r'active[:=]\s*(true|false|1|0)', query, re.IGNORECASE)
    if active_match:
        params["active"] = active_match.group(1).lower()
    
    last_updated_match = re.search(r'lastupdated[:=]\s*([\dT:-]+)', query, re.IGNORECASE)
    if last_updated_match:
        params["_lastUpdated"] = last_updated_match.group(1)
    
    type_match = re.search(r'type[:=]\s*([\w-]+)', query, re.IGNORECASE)
    if type_match:
        params["type"] = type_match.group(1)
    
    return count, params


class OrganizationMCP(BaseMCP):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")
        self.base_url = "https://gateway.api.esante.gouv.fr/fhir/Organization"

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this MCP"""
        return {
            "intents": ["find_organization", "find_hospital", "find_clinic"],
            "entities": ["name", "postal_code", "city", "type", "active"],
            "confidence_threshold": 0.5
        }

    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a natural language query to search for organizations.
        Makes direct FHIR API calls with smart parameter handling.
        """
        try:
            count, params = parse_organization_query(query)
            
            # Set up headers for FHIR API
            headers = {
                'ESANTE-API-KEY': self.api_key,
                'Accept': 'application/json'
            }
            
            # Add count parameter for API
            params['_count'] = str(min(count * 5, 100))  # Get more results to filter later
            
            print(f"[DEBUG] Making FHIR API call to {self.base_url} with params: {params}")
            
            try:
                response = requests.get(self.base_url, headers=headers, params=params, timeout=30)
                print(f"[DEBUG] API response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[ERROR] API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API returned {response.status_code}: {response.text}",
                        "results": []
                    }
                
                bundle = response.json()
                organizations = bundle.get("entry", [])
                
                if not organizations:
                    print(f"[DEBUG] No organizations found in response")
                    return {
                        "success": True,
                        "results": [],
                        "message": "No organizations found matching your criteria"
                    }
                
                # Parse and format results
                results = []
                for entry in organizations[:count]:
                    org = entry.get("resource", {})
                    
                    # Extract address information
                    addresses = org.get("address", [])
                    address_info = {}
                    if addresses:
                        addr = addresses[0]
                        address_info = {
                            "text": addr.get("text", ""),
                            "city": addr.get("city", ""),
                            "postalCode": addr.get("postalCode", ""),
                            "line": " ".join(addr.get("line", []))
                        }
                    
                    # Extract type information
                    org_type = None
                    type_info = org.get("type", [])
                    if type_info:
                        coding = type_info[0].get("coding", [])
                        if coding:
                            org_type = coding[0].get("display", coding[0].get("code", "Unknown"))
                    
                    results.append({
                        "id": org.get("id", ""),
                        "name": org.get("name", "Unknown Organization"),
                        "type": org_type,
                        "active": org.get("active", True),
                        "address": address_info,
                        "lastUpdated": org.get("meta", {}).get("lastUpdated", "")
                    })
                
                print(f"[DEBUG] Successfully parsed {len(results)} organizations")
                return {
                    "success": True,
                    "results": results,
                    "count": len(results)
                }
                
            except requests.exceptions.Timeout:
                return {
                    "success": False,
                    "error": "API request timed out",
                    "results": []
                }
            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": f"API request failed: {str(e)}",
                    "results": []
                }

        except Exception as e:
            print(f"[ERROR] Organization search failed: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to process query: {str(e)}",
                "results": []
            }

if __name__ == "__main__":
    # Create an instance of OrganizationMCP for testing
    mcp = OrganizationMCP()
    query = sys.argv[1] if len(sys.argv) > 1 else "find hospitals in Paris"
    result = mcp.process_query(query)
    print(result)
