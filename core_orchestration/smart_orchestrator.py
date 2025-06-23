"""
Smart Healthcare Search Orchestrator
Uses AI to interpret queries and orchestrate intelligent searches
"""

import asyncio
from typing import Dict, List, Any, Optional
from .ai_query_interpreter import AIQueryInterpreter
from .organization_mcp import OrganizationMCP
from .practitioner_role_mcp import PractitionerRoleMCP
import requests
import os

class SmartHealthcareOrchestrator:
    def __init__(self):
        self.ai_interpreter = AIQueryInterpreter()
        self.organization_mcp = OrganizationMCP()
        self.practitioner_mcp = PractitionerRoleMCP()
        self.api_key = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point - intelligently process any healthcare query
        """
        print(f"[SMART_DEBUG] Processing query: {user_query}")
        
        # Step 1: AI interpretation
        interpretation = self.ai_interpreter.synchronous_interpret_query(user_query)
        
        # Step 2: Execute search strategy
        if interpretation["search_strategy"]["parallel"]:
            return self._execute_parallel_search(interpretation)
        else:
            return self._execute_sequential_search(interpretation)
    
    def _execute_sequential_search(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute primary search with fallback"""
        primary_strategy = interpretation["search_strategy"]["primary"]
        fallback_strategy = interpretation["search_strategy"].get("fallback")
        
        print(f"[SMART_DEBUG] Executing {primary_strategy} search")
        
        # Try primary strategy
        if primary_strategy == "organization":
            result = self._search_organizations(interpretation["fhir_params"]["organization"])
        else:
            result = self._search_practitioners(interpretation["fhir_params"]["practitioner"])
        
        # If primary failed and we have fallback, try it
        if (not result.get("success") or len(result.get("results", [])) == 0) and fallback_strategy:
            print(f"[SMART_DEBUG] Primary search failed, trying fallback: {fallback_strategy}")
            
            if fallback_strategy == "organization":
                fallback_result = self._search_organizations(interpretation["fhir_params"]["organization"])
            else:
                fallback_result = self._search_practitioners(interpretation["fhir_params"]["practitioner"])
            
            if fallback_result.get("success") and len(fallback_result.get("results", [])) > 0:
                return self._format_response(fallback_result, interpretation, fallback_strategy)
        
        return self._format_response(result, interpretation, primary_strategy)
    
    def _execute_parallel_search(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute both organization and practitioner searches in parallel"""
        print(f"[SMART_DEBUG] Executing parallel search")
        
        # Execute both searches
        org_result = self._search_organizations(interpretation["fhir_params"]["organization"])
        prac_result = self._search_practitioners(interpretation["fhir_params"]["practitioner"])
        
        # Combine results intelligently
        combined_results = []
        
        if org_result.get("success") and org_result.get("results"):
            combined_results.extend(org_result["results"])
        
        if prac_result.get("success") and prac_result.get("results"):
            combined_results.extend(prac_result["results"])
        
        # Format combined response
        return {
            "success": len(combined_results) > 0,
            "results": combined_results,
            "count": len(combined_results),
            "search_type": "mixed",
            "ai_interpretation": interpretation,
            "message": f"Found {len(combined_results)} healthcare resources matching your criteria"
        }
    
    def _search_organizations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for organizations using clean FHIR parameters"""
        if not any(params.values()):  # No valid parameters
            return {"success": False, "results": [], "error": "No valid organization search parameters"}
        
        # Clean up parameters - remove None values
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            print(f"[SMART_DEBUG] Organization API call with params: {clean_params}")
            response = requests.get(
                "https://gateway.api.esante.gouv.fr/fhir/Organization",
                headers=headers,
                params=clean_params,
                timeout=30
            )
            
            if response.status_code != 200:
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            organizations = bundle.get("entry", [])
            
            # Format results
            results = []
            for entry in organizations:
                org = entry.get("resource", {})
                addresses = org.get("address", [])
                address_info = {}
                
                if addresses:
                    addr = addresses[0]
                    address_lines = addr.get("line", [])
                    clean_lines = [line for line in address_lines if line is not None]
                    address_info = {
                        "text": addr.get("text", ""),
                        "city": addr.get("city", ""),
                        "postalCode": addr.get("postalCode", ""),
                        "line": " ".join(clean_lines)
                    }
                
                org_type = None
                type_info = org.get("type", [])
                if type_info and type_info[0].get("coding"):
                    coding = type_info[0]["coding"][0]
                    org_type = coding.get("display", coding.get("code", "Unknown"))
                
                results.append({
                    "id": org.get("id", ""),
                    "name": org.get("name", "Unknown Organization"),
                    "type": org_type,
                    "active": org.get("active", True),
                    "address": address_info,
                    "lastUpdated": org.get("meta", {}).get("lastUpdated", ""),
                    "resource_type": "organization"
                })
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            print(f"[SMART_ERROR] Organization search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def _search_practitioners_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for practitioners by name using the Practitioner resource"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid practitioner name search parameters"}
        
        # Build search parameters for Practitioner resource
        clean_params = {"_count": "20"}  # More results for name searches
        
        # Handle name parameters
        if params.get("practitioner_name"):
            clean_params["name"] = params["practitioner_name"]
        elif params.get("family"):
            clean_params["family"] = params["family"]
        elif params.get("given"):
            clean_params["given"] = params["given"]
        
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            print(f"[SMART_DEBUG] Practitioner name search with params: {clean_params}")
            response = requests.get(
                "https://gateway.api.esante.gouv.fr/fhir/Practitioner",
                headers=headers,
                params=clean_params,
                timeout=30
            )
            
            print(f"[SMART_DEBUG] Practitioner name search response: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text[:200] if response.text else "No error details"
                print(f"[SMART_ERROR] API error {response.status_code}: {error_text}")
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            practitioners = bundle.get("entry", [])
            
            # Format results
            results = []
            for entry in practitioners:
                practitioner = entry.get("resource", {})
                
                # Extract name information
                names = practitioner.get("name", [])
                full_name = "Professionnel de santé"
                if names:
                    name_obj = names[0]
                    family = name_obj.get("family", "")
                    given_names = name_obj.get("given", [])
                    prefix = name_obj.get("prefix", [])
                    
                    name_parts = []
                    if prefix:
                        name_parts.extend(prefix)
                    if given_names:
                        name_parts.extend(given_names)
                    if family:
                        name_parts.append(family)
                    
                    full_name = " ".join(name_parts) if name_parts else "Professionnel de santé"
                
                # Extract identifiers
                identifiers = practitioner.get("identifier", [])
                rpps_id = ""
                for identifier in identifiers:
                    if "rpps" in identifier.get("system", "").lower():
                        rpps_id = identifier.get("value", "")
                        break
                
                results.append({
                    "id": practitioner.get("id", ""),
                    "name": full_name,
                    "specialty": "À déterminer",  # Would need PractitionerRole lookup
                    "active": practitioner.get("active", True),
                    "resource_type": "practitioner",
                    "rpps_id": rpps_id,
                    "address": {"note": "Recherche par nom - localisation via organisation"},
                    "practitioner_ref": f"Practitioner/{practitioner.get('id', '')}",
                    "search_type": "name"
                })
            
            print(f"[SMART_DEBUG] Found {len(results)} practitioners by name")
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            print(f"[SMART_ERROR] Practitioner name search failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "results": [], "error": str(e)}

    def _search_practitioners(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for practitioners using clean FHIR parameters"""
        if not any(params.values()):  # No valid parameters
            return {"success": False, "results": [], "error": "No valid practitioner search parameters"}
        
        # Map specialty names to profession codes (based on FHIR documentation)
        profession_codes = {
            "kiné": "40", "kine": "40", "kinésithérapeute": "40", "physiotherapist": "40",
            "osteopath": "50", "ostéopathe": "50", "osteopathe": "50",
            "cardiologue": "60", "cardiologist": "60",  # Most specialists use 60 or 95
            "dermatologue": "60", "dermatologist": "60", 
            "generaliste": "60", "médecin": "60", "medecin": "60", "general practitioner": "60",
            "dentiste": "86", "dentist": "86",
            "sage-femme": "31", "midwife": "31",
            "pharmacien": "96", "pharmacist": "96",
            "infirmier": "23", "nurse": "23"
        }
        
        # Build search parameters according to FHIR documentation
        clean_params = {"_count": "10"}  # Always limit results
        
        # Handle specialty/profession filtering
        if params.get("role"):
            # Direct role code from AI interpretation
            clean_params["role"] = str(params["role"])
            print(f"[SMART_DEBUG] Using direct role code: {params['role']}")
        elif params.get("specialty"):
            specialty_name = params["specialty"].lower()
            if specialty_name in profession_codes:
                clean_params["role"] = profession_codes[specialty_name]
                print(f"[SMART_DEBUG] Mapped specialty '{specialty_name}' to role '{profession_codes[specialty_name]}'")
            else:
                print(f"[SMART_DEBUG] Unknown specialty '{specialty_name}', using general search")
        
        # Note: FHIR API doesn't support direct city filtering for PractitionerRole
        # We'll return all results and let the frontend handle location display
        target_city = params.get("address-city")
        if target_city:
            print(f"[SMART_DEBUG] Note: City filtering requested for '{target_city}' - will return all results and enrich with organization data")
        
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            print(f"[SMART_DEBUG] Practitioner API call with params: {clean_params}")
            response = requests.get(
                "https://gateway.api.esante.gouv.fr/fhir/PractitionerRole",
                headers=headers,
                params=clean_params,
                timeout=30
            )
            
            print(f"[SMART_DEBUG] Practitioner API response: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text[:200] if response.text else "No error details"
                print(f"[SMART_ERROR] API error {response.status_code}: {error_text}")
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            practitioners = bundle.get("entry", [])
            
            # Format results with proper data extraction
            results = []
            for entry in practitioners:
                prac_role = entry.get("resource", {})
                
                # Extract practitioner reference and details
                practitioner_ref = prac_role.get("practitioner", {})
                practitioner_display = practitioner_ref.get("display")
                
                # If display is null, use the reference ID to create a meaningful name
                if not practitioner_display:
                    prac_ref = practitioner_ref.get("reference", "")
                    if prac_ref:
                        # Extract ID from reference like "Practitioner/12345"
                        prac_id = prac_ref.split("/")[-1] if "/" in prac_ref else prac_ref
                        practitioner_display = f"Professionnel de santé {prac_id}"
                    else:
                        practitioner_display = "Professionnel de santé"
                
                # Extract specialty/profession information from the code field
                code_info = prac_role.get("code", [])
                specialty_display = "General"
                profession_code = "Unknown"
                
                if code_info:
                    # Look for profession code in the coding array
                    for code_item in code_info:
                        coding_list = code_item.get("coding", [])
                        for coding in coding_list:
                            system = coding.get("system", "")
                            if "TRE-G15-ProfessionSante" in system:
                                profession_code = coding.get("code", "Unknown")
                                # Map code to display name (based on documentation)
                                code_map = {
                                    "60": "Médecin généraliste",
                                    "40": "Kinésithérapeute", 
                                    "50": "Ostéopathe",
                                    "86": "Dentiste",
                                    "31": "Sage-femme",
                                    "96": "Pharmacien",
                                    "23": "Infirmier"
                                }
                                specialty_display = code_map.get(profession_code, f"Profession {profession_code}")
                                break
                
                # Extract location/organization info safely
                location_info = prac_role.get("location")
                organization_info = prac_role.get("organization")
                
                address_info = {}
                if location_info:
                    address_info["location"] = location_info.get("display", location_info.get("reference", ""))
                if organization_info:
                    address_info["organization"] = organization_info.get("display", organization_info.get("reference", ""))
                
                # Create result entry
                result_entry = {
                    "id": prac_role.get("id", ""),
                    "name": practitioner_display,
                    "specialty": specialty_display,
                    "profession_code": profession_code,
                    "active": prac_role.get("active", True),
                    "resource_type": "practitioner",
                    "address": address_info,
                    "practitioner_ref": practitioner_ref.get("reference", ""),
                    "organization_ref": organization_info.get("reference", "") if organization_info else ""
                }
                
                # Add result to list (no city filtering for now due to API limitations)
                results.append(result_entry)
            
            print(f"[SMART_DEBUG] Found {len(results)} practitioners")
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            print(f"[SMART_ERROR] Practitioner search failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "results": [], "error": str(e)}
    
    def _format_response(self, result: Dict[str, Any], interpretation: Dict[str, Any], search_type: str) -> Dict[str, Any]:
        """Format the final response for the frontend"""
        if not result.get("success"):
            return {
                "success": False,
                "results": [],
                "error": result.get("error", "Search failed"),
                "ai_interpretation": interpretation
            }
        
        results = result.get("results", [])
        entity_type = "healthcare organizations" if search_type == "organization" else "healthcare professionals"
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "search_type": search_type,
            "ai_interpretation": interpretation,
            "message": f"Found {len(results)} {entity_type} matching your criteria"
        }
