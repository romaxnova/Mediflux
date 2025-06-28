"""
Smart Healthcare Search Orchestrator
Uses AI to interpret queries and orchestrate intelligent searches
"""

import asyncio
from typing import Dict, List, Any, Optional
from .ai_query_interpreter import AIQueryInterpreter
from .medication_toolkit import MedicationToolkit
import requests
import os

class SmartHealthcareOrchestrator:
    def __init__(self):
        self.ai_interpreter = AIQueryInterpreter()
        self.medication_toolkit = MedicationToolkit()
        self.api_key = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point - intelligently process any healthcare query
        """
        print(f"[SMART_DEBUG] Processing query: {user_query}")
        
        # Step 1: AI interpretation
        interpretation = self.ai_interpreter.synchronous_interpret_query(user_query)
        
        # Step 2: Enhance interpretation with orchestrator-level variable extraction
        # This ensures we carry forward the context throughout the workflow
        enhanced_interpretation = self._enhance_interpretation(user_query, interpretation)
        
        # Step 3: Execute search strategy with enhanced context
        if enhanced_interpretation["search_strategy"]["parallel"]:
            return self._execute_parallel_search(enhanced_interpretation)
        else:
            return self._execute_sequential_search(enhanced_interpretation)
    
    def _execute_sequential_search(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute primary search with fallback"""
        primary_strategy = interpretation["search_strategy"]["primary"]
        fallback_strategy = interpretation["search_strategy"].get("fallback")
        
        print(f"[SMART_DEBUG] Executing {primary_strategy} search")
        
        # Try primary strategy
        if primary_strategy == "organization":
            result = self._search_organizations(interpretation["fhir_params"]["organization"])
        elif primary_strategy == "medication":
            result = self._search_medications(interpretation["fhir_params"]["medication"])
        else:
            result = self._search_practitioners(interpretation["fhir_params"]["practitioner"])
        
        # If primary failed and we have fallback, try it
        if (not result.get("success") or len(result.get("results", [])) == 0) and fallback_strategy:
            print(f"[SMART_DEBUG] Primary search failed, trying fallback: {fallback_strategy}")
            
            if fallback_strategy == "organization":
                fallback_result = self._search_organizations(interpretation["fhir_params"]["organization"])
            elif fallback_strategy == "medication":
                fallback_result = self._search_medications(interpretation["fhir_params"]["medication"])
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
                "https://gateway.api.esante.gouv.fr/fhir/v1/Organization",
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
        """Search for practitioners by name using PractitionerRole endpoint (contains name data in extensions)"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid practitioner name search parameters"}
        
        # Extract search terms for name matching
        search_terms = []
        if params.get("family"):
            search_terms.append(params["family"].lower())
        if params.get("given"):
            given = params["given"][0] if isinstance(params["given"], list) else params["given"]
            search_terms.append(given.lower())
        elif params.get("name"):
            full_name = params["name"]
            search_terms.extend([part.lower() for part in full_name.split()])
        elif params.get("practitioner_name"):
            full_name = params["practitioner_name"]
            search_terms.extend([part.lower() for part in full_name.split()])
        
        if not search_terms:
            return {"success": False, "results": [], "error": "No valid name search terms provided"}
        
        print(f"[SMART_DEBUG] Name search using PractitionerRole endpoint with search terms: {search_terms}")
        
        # Use PractitionerRole endpoint with a larger count for name filtering
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            # Fetch PractitionerRole resources for name filtering
            response = requests.get(
                "https://gateway.api.esante.gouv.fr/fhir/v1/PractitionerRole",
                headers=headers,
                params={"_count": "100"},  # Get more results for name filtering
                timeout=30
            )
            
            print(f"[SMART_DEBUG] PractitionerRole response: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text[:200] if response.text else "No error details"
                print(f"[SMART_ERROR] API error {response.status_code}: {error_text}")
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            practitioner_roles = bundle.get("entry", [])
            
            print(f"[SMART_DEBUG] Found {len(practitioner_roles)} practitioner roles to filter by name")
            
            # Filter by name in extensions
            matching_results = []
            for entry in practitioner_roles:
                prac_role = entry.get("resource", {})
                
                # Extract name from extensions
                full_name = ""
                for ext in prac_role.get("extension", []):
                    if "PractitionerRole-Name" in ext.get("url", ""):
                        vh = ext.get("valueHumanName", {})
                        family = vh.get("family", "")
                        given = vh.get("given", [])
                        
                        # Construct full name
                        name_parts = []
                        if given:
                            name_parts.extend(given)
                        if family:
                            name_parts.append(family)
                        
                        if name_parts:
                            full_name = " ".join(name_parts)
                        break
                
                # Check if any search terms match the name
                if full_name:
                    full_name_lower = full_name.lower()
                    matches = [term for term in search_terms if term in full_name_lower]
                    
                    if matches:
                        print(f"[SMART_DEBUG] ✅ Found matching name: '{full_name}' (matched: {matches})")
                        
                        # Extract specialty/profession information
                        code_info = prac_role.get("code", [])
                        specialty_display = "Professionnel de santé"
                        profession_code = "Unknown"
                        
                        if code_info:
                            for code_item in code_info:
                                coding_list = code_item.get("coding", [])
                                for coding in coding_list:
                                    system = coding.get("system", "")
                                    if "TRE-G15-ProfessionSante" in system:
                                        profession_code = coding.get("code", "Unknown")
                                        # Map code to display name
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
                        
                        # Extract organization info
                        organization_info = prac_role.get("organization")
                        organization_ref = organization_info.get("reference", "") if organization_info else ""
                        
                        # Fetch organization details if available
                        organization_details = {"name": "Organisation inconnue", "address": {}}
                        if organization_ref:
                            organization_details = self._fetch_organization_details(organization_ref)
                        
                        # Extract practitioner reference for RPPS ID
                        practitioner_ref = prac_role.get("practitioner", {})
                        prac_ref = practitioner_ref.get("reference", "")
                        rpps_id = prac_ref.split("/")[-1] if "/" in prac_ref else ""
                        
                        matching_results.append({
                            "id": prac_role.get("id", ""),
                            "name": full_name,
                            "specialty": specialty_display,
                            "profession_code": profession_code,
                            "active": prac_role.get("active", True),
                            "resource_type": "practitioner",
                            "rpps_id": rpps_id,
                            "address": {
                                "organization_name": organization_details["name"],
                                "organization_address": organization_details["address"],
                                "full_location": organization_details["address"].get("full_address", "Localisation non disponible")
                            },
                            "search_type": "name"
                        })
                        
                        # Limit results to avoid too many matches
                        if len(matching_results) >= 10:
                            break
            
            print(f"[SMART_DEBUG] Name search completed - found {len(matching_results)} practitioners")
            
            if not matching_results:
                return {
                    "success": True,
                    "results": [],
                    "count": 0,
                    "message": f"No practitioners found matching the name '{' '.join(search_terms)}'. Try a different spelling or search by specialty."
                }
            
            return {
                "success": True,
                "results": matching_results,
                "count": len(matching_results)
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
        
        # Check if this is a specialty/role-based search FIRST (higher priority)
        specialty_params = ["specialty", "role"]
        has_specialty = any(params.get(param) for param in specialty_params)
        
        # Check if this is a name-based search
        name_params = ["practitioner_name", "family", "given", "name"]
        is_name_search = any(params.get(param) for param in name_params)
        
        # Route to name search ONLY if we have name params AND no specialty params
        if is_name_search and not has_specialty:
            print(f"[SMART_DEBUG] Detected name-based search (no specialty), routing to _search_practitioners_by_name")
            return self._search_practitioners_by_name(params)
        
        # Continue with specialty/role-based search
        print(f"[SMART_DEBUG] Detected specialty/role-based search, continuing with PractitionerRole endpoint")
        
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
        # Increase count for geographic filtering
        target_city = params.get("address-city")
        target_postal = params.get("address-postalcode")
        if target_city or target_postal:
            clean_params = {"_count": "100"}  # Get more results for geographic filtering
            print(f"[SMART_DEBUG] Geographic filtering requested - fetching 100 results for filtering")
        else:
            clean_params = {"_count": "10"}  # Normal count for non-geographic searches
        
        # Handle specialty/profession filtering
        if params.get("role"):
            # Direct role code from AI interpretation
            clean_params["role"] = str(params["role"])
            print(f"[SMART_DEBUG] Using direct role code: {params['role']}")
        elif params.get("specialty"):
            specialty_input = params["specialty"]
            # Check if it's already a numeric code
            if specialty_input.isdigit():
                clean_params["role"] = specialty_input
                print(f"[SMART_DEBUG] Using numeric specialty code: {specialty_input}")
            else:
                # Map specialty name to profession code
                specialty_name = specialty_input.lower()
                if specialty_name in profession_codes:
                    clean_params["role"] = profession_codes[specialty_name]
                    print(f"[SMART_DEBUG] Mapped specialty '{specialty_name}' to role '{profession_codes[specialty_name]}'")
                else:
                    print(f"[SMART_DEBUG] Unknown specialty '{specialty_name}', using general search")
        
        headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            print(f"[SMART_DEBUG] Practitioner API call with params: {clean_params}")
            response = requests.get(
                "https://gateway.api.esante.gouv.fr/fhir/v1/PractitionerRole",
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
                
                # Extract name from extensions (most efficient - no additional API calls)
                full_name = "Professionnel de santé"
                for ext in prac_role.get("extension", []):
                    if "PractitionerRole-Name" in ext.get("url", ""):
                        vh = ext.get("valueHumanName", {})
                        family = vh.get("family", "")
                        given = vh.get("given", [])
                        
                        # Construct full name
                        name_parts = []
                        if given:
                            name_parts.extend(given)
                        if family:
                            name_parts.append(family)
                        
                        if name_parts:
                            full_name = " ".join(name_parts)
                        break
                
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
                
                # Extract practitioner reference for RPPS ID
                practitioner_ref = prac_role.get("practitioner", {})
                prac_ref = practitioner_ref.get("reference", "")
                rpps_id = prac_ref.split("/")[-1] if "/" in prac_ref else ""
                
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
                    "name": full_name,
                    "specialty": specialty_display,
                    "profession_code": profession_code,
                    "active": prac_role.get("active", True),
                    "resource_type": "practitioner",
                    "address": address_info,
                    "practitioner_ref": practitioner_ref.get("reference", ""),
                    "organization_ref": organization_ref,
                    "rpps_id": rpps_id,
                    "organization_name": organization_details["name"]
                }
                
                # Add result to list
                results.append(result_entry)
            
            print(f"[SMART_DEBUG] Found {len(results)} practitioners before geographic filtering")
            
            # Apply geographic filtering if requested
            if target_city or target_postal:
                filtered_results = []
                for result in results:
                    org_address = result.get("address", {}).get("organization_address", {})
                    result_city = org_address.get("city", "").lower()
                    result_postal = org_address.get("postalCode", "")
                    
                    match_city = not target_city or target_city.lower() in result_city
                    match_postal = not target_postal or target_postal == result_postal
                    
                    if match_city and match_postal:
                        filtered_results.append(result)
                        if len(filtered_results) >= 10:  # Limit to 10 results
                            break
                
                results = filtered_results
                print(f"[SMART_DEBUG] After geographic filtering: {len(results)} practitioners in {target_city or target_postal}")
            
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
    
    def _search_medications(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for medications using the medication toolkit"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid medication search parameters"}
        
        try:
            search_type = params.get("search_type", "name")
            query = params.get("query", "")
            limit = int(params.get("limit", 10))
            
            print(f"[SMART_DEBUG] Medication search - Type: {search_type}, Query: {query}, Limit: {limit}")
            
            # Use medication toolkit based on search type
            if search_type == "name":
                result = self.medication_toolkit.search_by_name(query, limit)
            elif search_type == "substance":
                result = self.medication_toolkit.search_by_substance(query, limit)
            elif search_type == "cis_code":
                result = self.medication_toolkit.get_medication_details(query)
                # Convert single result to list format
                if result.get("success") and result.get("medication"):
                    result["medications"] = [result["medication"]]
            else:
                return {"success": False, "results": [], "error": f"Unknown search type: {search_type}"}
            
            if result.get("success"):
                # The medication toolkit already formats results properly
                # Just return them directly without re-formatting
                medications = result.get("results", [])  # Use "results" not "medications"
                
                return {
                    "success": True,
                    "results": medications,  # Already formatted by medication toolkit
                    "count": len(medications)
                }
            else:
                return {
                    "success": False,
                    "results": [],
                    "error": result.get("error", "Medication search failed")
                }
                
        except Exception as e:
            print(f"[SMART_ERROR] Medication search failed: {e}")
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
        
        # Determine entity type based on search type
        if search_type == "organization":
            entity_type = "healthcare organizations"
        elif search_type == "medication":
            entity_type = "medications"
        else:
            entity_type = "healthcare professionals"
        
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
                f"https://gateway.api.esante.gouv.fr/fhir/v1/Practitioner/{practitioner_id}",
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
                f"https://gateway.api.esante.gouv.fr/fhir/v1/Organization/{organization_id}",
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
    
    def _enhance_interpretation(self, user_query: str, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance AI interpretation with orchestrator-level context extraction
        This ensures proper variable carrying throughout the workflow
        """
        enhanced = interpretation.copy()
        
        # Extract key variables from the original query to avoid regex confusion
        query_lower = user_query.lower()
        
        # Import regex for pattern matching
        import re
        
        # Extract practitioner names more reliably by removing command words first
        clean_query = user_query
        command_patterns = [
            r'\bfind\s+',
            r'\bsearch\s+for\s+',
            r'\bsearch\s+',
            r'\bcherche\s+',
            r'\bshow\s+',
            r'\bget\s+',
            r'\blooking\s+for\s+',
            r'\bpour\s+un\s+',
            r'\bpour\s+'
        ]
        
        for pattern in command_patterns:
            clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE).strip()
        
        # Remove title prefixes (Dr, Doctor, etc.) but keep them for context
        title_patterns = [
            r'\b(?:dr\.?|docteur|doctor|prof\.?|professeur)\s+',
        ]
        
        for pattern in title_patterns:
            clean_query = re.sub(pattern, '', clean_query, flags=re.IGNORECASE).strip()
        
        # Look for proper names (capitalized words) in the cleaned query
        # Allow both single names (Bilbou) and full names (Nicolas Crail)
        name_matches = re.findall(r'\b([A-ZÁÉÈÊËÏÎÔÙÛÜŸÇ][a-záéèêëïîôùûüÿç\-]+(?:\s+[A-ZÁÉÈÊËÏÎÔÙÛÜŸÇa-záéèêëïîôùûüÿç\-]+)*)\b', clean_query, re.IGNORECASE)
        
        # Filter out non-name words that could be false positives
        organization_words = {'hospital', 'clinic', 'centre', 'center', 'cabinet', 'maison', 'hopital', 'hôpital', 'clinique'}
        location_words = {'paris', 'lyon', 'marseille', 'nice', 'toulouse', 'bordeaux', 'nantes', 'lille', 'strasbourg', 'montpellier', 'rennes'}
        general_words = {'find', 'search', 'doctor', 'docteur', 'medecin', 'médecin', 'in', 'dans', 'de', 'du', 'la', 'le', 'les', 'un', 'une'}
        
        practitioner_name = None
        if name_matches:
            # Filter matches to avoid false positives
            valid_names = []
            for match in name_matches:
                match_lower = match.lower()
                # Skip if it contains organization/location/general words
                if not any(word in match_lower for word in organization_words | location_words | general_words):
                    valid_names.append(match)
            
            if valid_names:
                # Take the longest valid match (most likely to be a full name)
                practitioner_name = max(valid_names, key=len).strip()
                print(f"[SMART_DEBUG] Enhanced extraction found name: '{practitioner_name}'")
        
        # Check if this looks like a name search but AI interpretation missed it
        # ONLY override if ALL of these conditions are met:
        # 1. We found a potential practitioner name
        # 2. AI didn't already correctly identify the intent as organization OR medication
        # 3. AI didn't populate practitioner_name
        # 4. The extracted name doesn't look like an organization name
        # 5. NOT a medication search (protect medication intents)
        if (practitioner_name and 
            enhanced.get("intent") not in ["organization", "medication"] and  # Don't override organization or medication searches
            not enhanced["fhir_params"]["practitioner"].get("practitioner_name") and
            not enhanced["extracted_entities"].get("organization_name")):  # Don't override if org name was detected
            
            # Additional check: make sure the name doesn't contain organization indicators
            org_indicators = ['cabinet', 'centre', 'center', 'clinique', 'clinic', 'hopital', 'hôpital', 'hospital', 'maison']
            name_lower = practitioner_name.lower()
            is_likely_org_name = any(indicator in name_lower for indicator in org_indicators)
            
            # Additional check: make sure it's not a medication name
            medication_indicators = ['doliprane', 'aspirin', 'aspirine', 'paracetamol', 'paracétamol', 'ibuprofen', 'ibuprofène']
            is_likely_medication = any(med in name_lower for med in medication_indicators)
            
            if not is_likely_org_name and not is_likely_medication:
                print(f"[SMART_DEBUG] AI missed name '{practitioner_name}', enhancing interpretation")
                
                # Split name into components
                name_parts = practitioner_name.split()
                if len(name_parts) == 1:
                    # Single name - treat as family name for broader search
                    family_name = name_parts[0]
                    given_name = ""
                else:
                    # Multiple parts - last is family, rest are given names
                    family_name = name_parts[-1]
                    given_name = " ".join(name_parts[:-1])
                
                # Update the interpretation
                enhanced["extracted_entities"]["practitioner_name"] = practitioner_name
                enhanced["fhir_params"]["practitioner"]["practitioner_name"] = practitioner_name
                enhanced["fhir_params"]["practitioner"]["name"] = practitioner_name
                enhanced["fhir_params"]["practitioner"]["family"] = family_name
                enhanced["fhir_params"]["practitioner"]["given"] = given_name if given_name else None
                
                # Ensure it's routed as a practitioner search
                enhanced["intent"] = "practitioner"
                enhanced["search_strategy"]["primary"] = "practitioner"
                enhanced["confidence"] = max(enhanced.get("confidence", 0.5), 0.85)
                
                print(f"[SMART_DEBUG] Enhanced params: family='{family_name}', given='{given_name or 'None'}'")
            else:
                print(f"[SMART_DEBUG] Detected name '{practitioner_name}' looks like organization name, not overriding")
        
        # OVERRIDE fallback interpretation if we have better extraction
        # ONLY if AI didn't already correctly identify intent as organization or medication
        elif (practitioner_name and 
              enhanced["fhir_params"]["practitioner"].get("practitioner_name") and 
              enhanced.get("intent") not in ["organization", "medication"] and  # Don't override organization or medication searches
              not enhanced["extracted_entities"].get("organization_name")):
            current_name = enhanced["fhir_params"]["practitioner"]["practitioner_name"]
            
            # Additional check: make sure it's not a medication name
            medication_indicators = ['doliprane', 'aspirin', 'aspirine', 'paracetamol', 'paracétamol', 'ibuprofen', 'ibuprofène']
            is_likely_medication = any(med in practitioner_name.lower() for med in medication_indicators)
            
            if is_likely_medication:
                print(f"[SMART_DEBUG] Detected '{practitioner_name}' as medication name, not overriding")
            else:
                # Override if names are different AND enhanced extraction is cleaner
                # (doesn't contain titles, command words, etc.)
                should_override = (
                    practitioner_name != current_name and (
                        len(practitioner_name) > len(current_name) or  # Enhanced is longer
                        not re.search(r'\b(?:dr\.?|docteur|doctor|find|search)\b', practitioner_name, re.IGNORECASE)  # Enhanced is cleaner
                    )
                )
                
                if should_override:
                    print(f"[SMART_DEBUG] Overriding fallback name '{current_name}' with better extraction '{practitioner_name}'")
                    
                    # Split name into components
                    name_parts = practitioner_name.split()
                    if len(name_parts) == 1:
                        # Single name - treat as family name for broader search
                        family_name = name_parts[0]
                        given_name = ""
                    else:
                        # Multiple parts - last is family, rest are given names
                        family_name = name_parts[-1]
                        given_name = " ".join(name_parts[:-1])
                    
                    # Update with better interpretation
                    enhanced["extracted_entities"]["practitioner_name"] = practitioner_name
                    enhanced["fhir_params"]["practitioner"]["practitioner_name"] = practitioner_name
                    enhanced["fhir_params"]["practitioner"]["name"] = practitioner_name
                    enhanced["fhir_params"]["practitioner"]["family"] = family_name
                    enhanced["fhir_params"]["practitioner"]["given"] = given_name if given_name else None
                    
                    print(f"[SMART_DEBUG] Corrected params: family='{family_name}', given='{given_name or 'None'}'")
        else:
            if practitioner_name and enhanced.get("intent") in ["organization", "medication"]:
                intent_type = enhanced.get("intent")
                print(f"[SMART_DEBUG] Found name '{practitioner_name}' but AI correctly identified {intent_type} intent - respecting AI decision")
        
        # Extract location information that might have been missed
        postal_match = re.search(r'\b(\d{5})\b', user_query)
        if postal_match and not enhanced["fhir_params"]["practitioner"].get("address-postalcode"):
            postal_code = postal_match.group(1)
            enhanced["fhir_params"]["practitioner"]["address-postalcode"] = postal_code
            enhanced["fhir_params"]["organization"]["address-postalcode"] = postal_code
            print(f"[SMART_DEBUG] Enhanced extraction found postal code: {postal_code}")
        
        # Extract city information
        city_patterns = [
            r'\b(paris|lyon|marseille|nice|toulouse|bordeaux|nantes|lille|strasbourg|montpellier|rennes)\b',
            r'\b(75\d{3}|13\d{3}|69\d{3}|06\d{3}|31\d{3}|33\d{3}|44\d{3}|59\d{3}|67\d{3}|34\d{3}|35\d{3})\b'
        ]
        
        for pattern in city_patterns:
            city_match = re.search(pattern, query_lower)
            if city_match and not enhanced["fhir_params"]["practitioner"].get("address-city"):
                city = city_match.group(1).title()
                enhanced["fhir_params"]["practitioner"]["address-city"] = city
                enhanced["fhir_params"]["organization"]["address-city"] = city
                print(f"[SMART_DEBUG] Enhanced extraction found city: {city}")
                break
        
        return enhanced
