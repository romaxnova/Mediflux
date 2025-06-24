"""
Smart Healthcare Search Orchestrator
Uses AI to interpret queries and orchestrate intelligent searches
"""

import asyncio
from typing import Dict, List, Any, Optional
from .ai_query_interpreter import AIQueryInterpreter
import requests
import os

class SmartHealthcareOrchestrator:
    def __init__(self):
        self.ai_interpreter = AIQueryInterpreter()
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
        """Search for practitioners by name using the PractitionerRole resource with extensions"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid practitioner name search parameters"}
        
        # Extract the search name
        search_name = None
        if params.get("name"):
            search_name = params["name"]
        elif params.get("practitioner_name"):
            search_name = params["practitioner_name"]
        elif params.get("family"):
            search_name = params["family"]
        elif params.get("given"):
            search_name = params["given"]
        
        if not search_name:
            return {"success": False, "results": [], "error": "No name parameter provided"}
        
        # Use PractitionerRole endpoint to get name extensions
        clean_params = {"_count": "50"}  # More results for name filtering
        
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            print(f"[SMART_DEBUG] Practitioner name search using PractitionerRole with filter: '{search_name}'")
            response = requests.get(
                "https://gateway.api.esante.gouv.fr/fhir/PractitionerRole",
                headers=headers,
                params=clean_params,
                timeout=30
            )
            
            print(f"[SMART_DEBUG] PractitionerRole response: {response.status_code}")
            if response.text:
                print(f"[SMART_DEBUG] Response size: {len(response.text)} characters")
            
            if response.status_code != 200:
                error_text = response.text[:200] if response.text else "No error details"
                print(f"[SMART_ERROR] API error {response.status_code}: {error_text}")
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            practitioner_roles = bundle.get("entry", [])
            
            print(f"[SMART_DEBUG] Got {len(practitioner_roles)} total practitioner roles from API")
            
            # Debug: Log first few entries to see the actual structure
            if practitioner_roles:
                print(f"[SMART_DEBUG] Sample entry structure:")
                sample_entry = practitioner_roles[0].get("resource", {})
                print(f"[SMART_DEBUG] Sample ID: {sample_entry.get('id', 'N/A')}")
                print(f"[SMART_DEBUG] Sample extensions count: {len(sample_entry.get('extension', []))}")
                print(f"[SMART_DEBUG] Sample practitioner ref: {sample_entry.get('practitioner', {})}")
                
                # Debug the extensions to see what's actually there
                for i, ext in enumerate(sample_entry.get("extension", [])[:3]):  # First 3 extensions
                    print(f"[SMART_DEBUG] Extension {i}: URL={ext.get('url', 'N/A')}, Keys={list(ext.keys())}")
            
            # Filter results by name locally
            search_name_lower = search_name.lower()
            results = []
            
            for entry in practitioner_roles:
                prac_role = entry.get("resource", {})
                
                print(f"[SMART_DEBUG] Processing practitioner role ID: {prac_role.get('id', 'unknown')}")
                
                # Extract name from extensions
                full_name = None
                found_extension = False
                for ext in prac_role.get("extension", []):
                    found_extension = True
                    print(f"[SMART_DEBUG] Checking extension URL: {ext.get('url', 'N/A')}")
                    if "PractitionerRole-Name" in ext.get("url", ""):
                        vh = ext.get("valueHumanName", {})
                        family = vh.get("family", "")
                        given = vh.get("given", [])
                        
                        print(f"[SMART_DEBUG] Found name extension - Family: {family}, Given: {given}")
                        
                        # Construct full name
                        name_parts = []
                        if given:
                            name_parts.extend(given)
                        if family:
                            name_parts.append(family)
                        
                        if name_parts:
                            full_name = " ".join(name_parts)
                            break
                
                if not found_extension:
                    print(f"[SMART_DEBUG] No extensions found for this entry")
                
                # Skip if no name found
                if not full_name:
                    print(f"[SMART_DEBUG] No full name found, skipping this entry")
                    continue
                
                print(f"[SMART_DEBUG] Found name: '{full_name}', checking against search: '{search_name_lower}'")
                
                # Filter by search name
                if search_name_lower not in full_name.lower():
                    print(f"[SMART_DEBUG] Name doesn't match, skipping")
                    continue
                
                print(f"[SMART_DEBUG] Name matches! Processing this entry...")
                
                # Extract practitioner reference and other details
                practitioner_ref = prac_role.get("practitioner", {})
                practitioner_id = practitioner_ref.get("reference", "").split("/")[-1] if practitioner_ref.get("reference") else ""
                
                # Extract profession info
                specialty_display = "Professionnel de santé"
                profession_code = "Unknown"
                
                code_info = prac_role.get("code", [])
                if code_info:
                    for code_item in code_info:
                        coding_list = code_item.get("coding", [])
                        for coding in coding_list:
                            system = coding.get("system", "")
                            if "TRE-G15-ProfessionSante" in system:
                                profession_code = coding.get("code", "Unknown")
                                code_map = {
                                    "60": "Médecin généraliste",
                                    "40": "Kinésithérapeute", 
                                    "50": "Ostéopathe",
                                    "86": "Dentiste",
                                    "31": "Sage-femme",
                                    "96": "Pharmacien",
                                    "23": "Infirmier",
                                    "54": "Chiropracteur"
                                }
                                specialty_display = code_map.get(profession_code, f"Profession {profession_code}")
                                break
                
                # Get organization details
                organization_ref = prac_role.get("organization", {}).get("reference", "") if prac_role.get("organization") else ""
                organization_details = {"name": "Organisation inconnue", "address": {}}
                if organization_ref:
                    organization_details = self._fetch_organization_details(organization_ref)
                
                results.append({
                    "id": prac_role.get("id", ""),
                    "name": full_name,
                    "specialty": specialty_display,
                    "profession_code": profession_code,
                    "active": prac_role.get("active", True),
                    "resource_type": "practitioner",
                    "rpps_id": practitioner_id,
                    "address": {
                        "organization_name": organization_details["name"],
                        "organization_address": organization_details["address"],
                        "full_location": organization_details["address"].get("full_address", "Localisation non disponible")
                    },
                    "practitioner_ref": practitioner_ref.get("reference", ""),
                    "organization_ref": organization_ref,
                    "organization_name": organization_details["name"],
                    "search_type": "name"
                })
            
            print(f"[SMART_DEBUG] Found {len(results)} practitioners matching name '{search_name}'")
            
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
        
        # Check if this is a name-based search and route accordingly
        name_params = ["practitioner_name", "family", "given", "name"]
        is_name_search = any(params.get(param) for param in name_params)
        
        if is_name_search:
            print(f"[SMART_DEBUG] Detected name-based search, routing to _search_practitioners_by_name")
            return self._search_practitioners_by_name(params)
        
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
            "infirmier": "23", "nurse": "23",
            "chiropracteur": "54", "chiropractor": "54"
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
                                    "23": "Infirmier",
                                    "54": "Chiropracteur"
                                }
                                specialty_display = code_map.get(profession_code, f"Profession {profession_code}")
                                break
                
                # Extract organization info safely
                organization_info = prac_role.get("organization")
                organization_ref = organization_info.get("reference", "") if organization_info else ""
                
                # Fetch detailed practitioner information
                practitioner_details = self._fetch_practitioner_details(practitioner_ref.get("reference", ""))
                
                # Fetch organization details if available
                organization_details = {"name": "Organisation inconnue", "address": {}}
                if organization_ref:
                    organization_details = self._fetch_organization_details(organization_ref)
                
                # Create comprehensive address info
                address_info = {
                    "organization_name": organization_details["name"],
                    "organization_address": organization_details["address"],
                    "full_location": organization_details["address"].get("full_address", "Localisation non disponible")
                }
                
                # Create result entry with enriched data
                result_entry = {
                    "id": prac_role.get("id", ""),
                    "name": practitioner_details["name"],
                    "specialty": specialty_display,
                    "profession_code": profession_code,
                    "active": prac_role.get("active", True),
                    "resource_type": "practitioner",
                    "address": address_info,
                    "practitioner_ref": practitioner_ref.get("reference", ""),
                    "organization_ref": organization_ref,
                    "rpps_id": practitioner_details["rpps_id"],
                    "organization_name": organization_details["name"]
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
    
    def _fetch_practitioner_details(self, practitioner_ref: str) -> Dict[str, Any]:
        """Fetch detailed practitioner information using the Practitioner API"""
        if not practitioner_ref or not practitioner_ref.startswith("Practitioner/"):
            return {"name": "Professionnel de santé", "rpps_id": ""}
        
        practitioner_id = practitioner_ref.split("/")[-1]
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(
                f"https://gateway.api.esante.gouv.fr/fhir/Practitioner/{practitioner_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                practitioner = response.json()
                
                # Extract name information
                names = practitioner.get("name", [])
                full_name = "Professionnel de santé"
                
                if names:
                    name_obj = names[0]
                    family = name_obj.get("family", "")
                    given_names = name_obj.get("given", [])
                    prefix = name_obj.get("prefix", [])
                    
                    name_parts = []
                    if given_names:
                        name_parts.extend(given_names)
                    if family:
                        name_parts.append(family.upper())
                    if prefix:
                        # Add prefix at the beginning for titles like Dr., etc.
                        name_parts = list(prefix) + name_parts
                    
                    if name_parts:
                        full_name = " ".join(name_parts)
                    else:
                        # Fallback to just family name if that's all we have
                        full_name = family.upper() if family else "Professionnel de santé"
                
                # Extract RPPS ID
                identifiers = practitioner.get("identifier", [])
                rpps_id = ""
                for identifier in identifiers:
                    if "rpps" in identifier.get("system", "").lower():
                        rpps_id = identifier.get("value", "")
                        break
                
                return {"name": full_name, "rpps_id": rpps_id}
                
        except Exception as e:
            print(f"[SMART_DEBUG] Failed to fetch practitioner details for {practitioner_id}: {e}")
        
        return {"name": f"Professionnel de santé {practitioner_id}", "rpps_id": ""}
    
    def _fetch_organization_details(self, organization_ref: str) -> Dict[str, Any]:
        """Fetch organization details using the Organization API"""
        if not organization_ref or not organization_ref.startswith("Organization/"):
            return {"name": "Organisation inconnue", "address": {}}
        
        organization_id = organization_ref.split("/")[-1]
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(
                f"https://gateway.api.esante.gouv.fr/fhir/Organization/{organization_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                organization = response.json()
                
                org_name = organization.get("name", "Organisation inconnue")
                
                # Extract address information
                addresses = organization.get("address", [])
                address_info = {}
                
                if addresses:
                    addr = addresses[0]
                    address_lines = addr.get("line", [])
                    clean_lines = [line for line in address_lines if line is not None]
                    address_info = {
                        "text": addr.get("text", ""),
                        "city": addr.get("city", ""),
                        "postalCode": addr.get("postalCode", ""),
                        "line": " ".join(clean_lines),
                        "full_address": f"{' '.join(clean_lines)}, {addr.get('postalCode', '')} {addr.get('city', '')}".strip()
                    }
                
                return {"name": org_name, "address": address_info}
                
        except Exception as e:
            print(f"[SMART_DEBUG] Failed to fetch organization details for {organization_id}: {e}")
        
        return {"name": f"Organisation {organization_id}", "address": {}}
