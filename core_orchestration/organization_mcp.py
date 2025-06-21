import requests
import re
from typing import Dict, Any
import sys
import os
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
    m = re.search(r"(?:last|give me|show me|find|list)?\s*(\d+)?\s*([\w'-éèêàçôîûïüöäëâù ]+)?\s*(?:from|in)?\s*(\d{5})?", query, re.IGNORECASE)
    if m:
        if m.group(1):
            count = int(m.group(1))
        if m.group(2):
            phrase = m.group(2).strip().lower()
            # Try to match as name or type
            params["name"] = phrase
        if m.group(3):
            params["address-postalcode"] = m.group(3)
    # Arrondissement/Paris logic
    if "address-postalcode" not in params:
        postal_code = arrondissement_to_postal(query)
        if postal_code:
            params["address-postalcode"] = postal_code
    # Address/city
    m = re.search(r"in ([a-zA-Z\s\-\’]+)$", query, re.IGNORECASE)
    if m:
        params["address-city"] = m.group(1).strip()
    # FHIR modifiers (e.g. name:exact, identifier:contains)
    modifier_matches = re.findall(r"(\w+):(exact|contains|missing|text) ([^\s]+)", query)
    for field, modifier, value in modifier_matches:
        params[f"{field}:{modifier}"] = value
    # FHIR _id, identifier, active, type, _lastUpdated
    id_match = re.search(r"id[:= ]([\w-]+)", query)
    if id_match:
        params["_id"] = id_match.group(1)
    identifier_match = re.search(r"identifier[:= ]([\w-]+)", query)
    if identifier_match:
        params["identifier"] = identifier_match.group(1)
    active_match = re.search(r"active[:= ](true|false|1|0)", query, re.IGNORECASE)
    if active_match:
        params["active"] = active_match.group(1).lower()
    last_updated_match = re.search(r"lastupdated[:= ]([\dT:-]+)", query, re.IGNORECASE)
    if last_updated_match:
        params["_lastUpdated"] = last_updated_match.group(1)
    type_match = re.search(r"type[:= ]([\w-]+)", query, re.IGNORECASE)
    if type_match:
        params["type"] = type_match.group(1)
    return count, params


class OrganizationMCP(BaseMCP):
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
        Handles error cases and returns results in a standardized format.
        """
        try:
            count, params = parse_organization_query(query)

            endpoints = [
                "http://0.0.0.0:8000/api/Organization/search",
                "http://0.0.0.0:8000/api/organization/search"
            ]

            results = []
            last_error = None

            for endpoint in endpoints:
                try:
                    print(f"[DEBUG] Trying endpoint {endpoint} with params {params}")
                    resp = requests.get(endpoint, params=params)

                    if resp.status_code == 404:
                        last_error = f"404 Not Found for {endpoint} with params {params}"
                        continue

                    resp.raise_for_status()
                    bundle = resp.json()
                    orgs = bundle.get("entry", bundle.get("results", []))[:count]

                    if not orgs:
                        continue

                    for org in orgs:
                        o = org.get("resource", org)
                        extensions = o.get("extension", [])
                        extension_data = {}

                        for ext in extensions:
                            url = ext.get("url")
                            if "address" in url or "finess" in url.lower():
                                extension_data["address"] = ext.get("valueString", "N/A")
                            elif "contact" in url.lower():
                                extension_data["contact"] = ext.get("valueString", "N/A")

                        results.append({
                            "name": o.get("name", "Unknown"),
                            "address": extension_data.get("address",
                                o.get("address", [{}])[0].get("text") if o.get("address") else "n/a"),
                            "active": o.get("active", "n/a"),
                            "type": o.get("type", [{}])[0].get("coding", [{}])[0].get("code") if o.get("type") else None,
                            "extensions": extension_data
                        })

                    if results:
                        return {
                            "success": True,
                            "results": results
                        }

                except Exception as e:
                    last_error = str(e)
                    continue

            return {
                "success": False,
                "error": f"Organization search failed: {last_error}",
                "results": []
            }

        except Exception as e:
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
