"""
Comprehensive Healthcare Search Orchestrator
Efficiently leverages all 5 FHIR resources with intelligent query routing
"""

import asyncio
from typing import Dict, List, Any, Optional
from .ai_query_interpreter_v2 import EnhancedAIQueryInterpreter
import requests
import os
import json

class ComprehensiveHealthcareOrchestrator:
    def __init__(self):
        self.ai_interpreter = EnhancedAIQueryInterpreter()
        self.api_key = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")
        self.base_url = "https://gateway.api.esante.gouv.fr/fhir"
        self.headers = {
            'ESANTE-API-KEY': self.api_key,
            'Accept': 'application/json'
        }
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point - intelligently process any healthcare query using all FHIR resources
        """
        print(f"[COMPREHENSIVE_DEBUG] Processing query: {user_query}")
        
        # Step 1: AI interpretation
        interpretation = self.ai_interpreter.synchronous_interpret_query(user_query)
        
        # Step 2: Execute search strategy
        if interpretation["search_strategy"].get("parallel"):
            return self._execute_parallel_search(interpretation)
        else:
            return self._execute_sequential_search(interpretation)
    
    def _execute_sequential_search(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute primary search with intelligent fallbacks"""
        primary_strategy = interpretation["search_strategy"]["primary"]
        secondary_strategies = interpretation["search_strategy"].get("secondary", [])
        
        print(f"[COMPREHENSIVE_DEBUG] Executing {primary_strategy} search")
        
        # Try primary strategy
        result = self._execute_resource_search(primary_strategy, interpretation["fhir_params"])
        
        # If primary failed and we have fallbacks, try them
        if (not result.get("success") or len(result.get("results", [])) == 0) and secondary_strategies:
            for fallback_strategy in secondary_strategies:
                print(f"[COMPREHENSIVE_DEBUG] Trying fallback: {fallback_strategy}")
                
                fallback_result = self._execute_resource_search(fallback_strategy, interpretation["fhir_params"])
                
                if fallback_result.get("success") and len(fallback_result.get("results", [])) > 0:
                    return self._format_response(fallback_result, interpretation, fallback_strategy)
        
        return self._format_response(result, interpretation, primary_strategy)
    
    def _execute_parallel_search(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple resource searches in parallel"""
        print(f"[COMPREHENSIVE_DEBUG] Executing parallel search")
        
        primary_strategy = interpretation["search_strategy"]["primary"]
        secondary_strategies = interpretation["search_strategy"].get("secondary", [])
        
        # Execute searches
        results = {}
        
        # Primary search
        results[primary_strategy] = self._execute_resource_search(primary_strategy, interpretation["fhir_params"])
        
        # Secondary searches
        for strategy in secondary_strategies:
            results[strategy] = self._execute_resource_search(strategy, interpretation["fhir_params"])
        
        # Combine results intelligently
        return self._combine_parallel_results(results, interpretation)
    
    def _execute_resource_search(self, resource_type: str, fhir_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search for a specific FHIR resource"""
        
        search_methods = {
            "organization": self._search_organizations,
            "practitioner_role": self._search_practitioner_roles,
            "practitioner_name": self._search_practitioners_by_name,
            "healthcare_service": self._search_healthcare_services,
            "device": self._search_devices
        }
        
        search_method = search_methods.get(resource_type)
        if not search_method:
            return {"success": False, "results": [], "error": f"Unknown resource type: {resource_type}"}
        
        params = fhir_params.get(resource_type, {})
        return search_method(params)
    
    def _search_organizations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Organization resource"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid organization parameters"}
        
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        try:
            print(f"[COMPREHENSIVE_DEBUG] Organization search: {clean_params}")
            response = requests.get(f"{self.base_url}/Organization", headers=self.headers, params=clean_params, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            organizations = bundle.get("entry", [])
            
            results = []
            for entry in organizations:
                org = entry.get("resource", {})
                
                # Extract address
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
                
                # Extract organization type
                org_type = "Organisation de santé"
                type_info = org.get("type", [])
                if type_info and type_info[0].get("coding"):
                    coding = type_info[0]["coding"][0]
                    org_type = coding.get("display", coding.get("code", "Organisation de santé"))
                
                results.append({
                    "id": org.get("id", ""),
                    "name": org.get("name", "Organisation inconnue"),
                    "type": org_type,
                    "active": org.get("active", True),
                    "address": address_info,
                    "lastUpdated": org.get("meta", {}).get("lastUpdated", ""),
                    "resource_type": "organization"
                })
            
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            print(f"[COMPREHENSIVE_ERROR] Organization search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def _search_practitioner_roles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search PractitionerRole resource with intelligent filtering"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid practitioner role parameters"}
        
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        try:
            print(f"[COMPREHENSIVE_DEBUG] PractitionerRole search: {clean_params}")
            response = requests.get(f"{self.base_url}/PractitionerRole", headers=self.headers, params=clean_params, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            practitioner_roles = bundle.get("entry", [])
            
            results = []
            for entry in practitioner_roles:
                prac_role = entry.get("resource", {})
                
                # Extract practitioner info
                practitioner_ref = prac_role.get("practitioner", {})
                practitioner_display = practitioner_ref.get("display") or f"Professionnel {practitioner_ref.get('reference', '').split('/')[-1]}"
                
                # Extract specialty/role
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
                                
                                # Map code to display name
                                code_map = {
                                    "60": "Médecin généraliste",
                                    "40": "Kinésithérapeute", 
                                    "86": "Dentiste",
                                    "31": "Sage-femme",
                                    "96": "Pharmacien",
                                    "23": "Infirmier",
                                    "50": "Ostéopathe"
                                }
                                specialty_display = code_map.get(profession_code, f"Profession {profession_code}")
                                break
                
                # Extract organization info
                organization_refs = prac_role.get("organization", [])
                location_refs = prac_role.get("location", [])
                
                address_info = {}
                if organization_refs:
                    address_info["organization"] = organization_refs[0].get("display", "")
                if location_refs:
                    address_info["location"] = location_refs[0].get("display", "")
                
                results.append({
                    "id": prac_role.get("id", ""),
                    "name": practitioner_display,
                    "specialty": specialty_display,
                    "profession_code": profession_code,
                    "active": prac_role.get("active", True),
                    "resource_type": "practitioner",
                    "address": address_info,
                    "practitioner_ref": practitioner_ref.get("reference", ""),
                    "organization_ref": organization_refs[0].get("reference", "") if organization_refs else ""
                })
            
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            print(f"[COMPREHENSIVE_ERROR] PractitionerRole search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def _search_practitioners_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Practitioner resource by name"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid practitioner name parameters"}
        
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        try:
            print(f"[COMPREHENSIVE_DEBUG] Practitioner name search: {clean_params}")
            response = requests.get(f"{self.base_url}/Practitioner", headers=self.headers, params=clean_params, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            practitioners = bundle.get("entry", [])
            
            results = []
            for entry in practitioners:
                practitioner = entry.get("resource", {})
                
                # Extract name
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
                    "specialty": "À déterminer",
                    "active": practitioner.get("active", True),
                    "resource_type": "practitioner",
                    "rpps_id": rpps_id,
                    "address": {"note": "Recherche par nom"},
                    "practitioner_ref": f"Practitioner/{practitioner.get('id', '')}",
                    "search_type": "name"
                })
            
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            print(f"[COMPREHENSIVE_ERROR] Practitioner name search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def _search_healthcare_services(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search HealthcareService resource"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid healthcare service parameters"}
        
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        try:
            print(f"[COMPREHENSIVE_DEBUG] HealthcareService search: {clean_params}")
            response = requests.get(f"{self.base_url}/HealthcareService", headers=self.headers, params=clean_params, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            services = bundle.get("entry", [])
            
            results = []
            for entry in services:
                service = entry.get("resource", {})
                
                # Extract service info
                name = service.get("name", "Service de santé")
                
                # Extract category and type
                categories = service.get("category", [])
                service_types = service.get("type", [])
                
                category_display = "Service général"
                if categories and categories[0].get("coding"):
                    category_display = categories[0]["coding"][0].get("display", "Service général")
                
                type_display = ""
                if service_types and service_types[0].get("coding"):
                    type_display = service_types[0]["coding"][0].get("display", "")
                
                # Extract organization
                organization_ref = service.get("providedBy", {})
                organization_display = organization_ref.get("display", "")
                
                results.append({
                    "id": service.get("id", ""),
                    "name": name,
                    "category": category_display,
                    "type": type_display,
                    "organization": organization_display,
                    "active": service.get("active", True),
                    "resource_type": "healthcare_service",
                    "organization_ref": organization_ref.get("reference", "")
                })
            
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            print(f"[COMPREHENSIVE_ERROR] HealthcareService search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def _search_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search Device resource"""
        if not any(params.values()):
            return {"success": False, "results": [], "error": "No valid device parameters"}
        
        clean_params = {k: v for k, v in params.items() if v is not None}
        
        try:
            print(f"[COMPREHENSIVE_DEBUG] Device search: {clean_params}")
            response = requests.get(f"{self.base_url}/Device", headers=self.headers, params=clean_params, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "results": [], "error": f"API error: {response.status_code}"}
            
            bundle = response.json()
            devices = bundle.get("entry", [])
            
            results = []
            for entry in devices:
                device = entry.get("resource", {})
                
                # Extract device info
                device_name = device.get("deviceName", [])
                name = "Équipement médical"
                if device_name:
                    name = device_name[0].get("name", "Équipement médical")
                
                # Extract type
                device_type = device.get("type", {})
                type_display = "Équipement"
                if device_type.get("coding"):
                    type_display = device_type["coding"][0].get("display", "Équipement")
                
                # Extract organization
                organization_ref = device.get("owner", {})
                organization_display = organization_ref.get("display", "")
                
                results.append({
                    "id": device.get("id", ""),
                    "name": name,
                    "type": type_display,
                    "status": device.get("status", "unknown"),
                    "organization": organization_display,
                    "resource_type": "device",
                    "organization_ref": organization_ref.get("reference", "")
                })
            
            return {"success": True, "results": results, "count": len(results)}
            
        except Exception as e:
            print(f"[COMPREHENSIVE_ERROR] Device search failed: {e}")
            return {"success": False, "results": [], "error": str(e)}
    
    def _combine_parallel_results(self, results: Dict[str, Dict[str, Any]], interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently combine results from parallel searches"""
        combined_results = []
        total_count = 0
        
        # Prioritize results based on primary strategy
        primary_strategy = interpretation["search_strategy"]["primary"]
        
        # Add primary results first
        if primary_strategy in results and results[primary_strategy].get("success"):
            primary_results = results[primary_strategy].get("results", [])
            combined_results.extend(primary_results)
            total_count += len(primary_results)
        
        # Add secondary results
        for strategy, result in results.items():
            if strategy != primary_strategy and result.get("success"):
                secondary_results = result.get("results", [])
                combined_results.extend(secondary_results)
                total_count += len(secondary_results)
        
        # Determine search type for response
        resource_types = list(set([r.get("resource_type", "unknown") for r in combined_results]))
        search_type = "mixed" if len(resource_types) > 1 else resource_types[0] if resource_types else "unknown"
        
        return {
            "success": total_count > 0,
            "results": combined_results,
            "count": total_count,
            "search_type": search_type,
            "ai_interpretation": interpretation,
            "message": f"Trouvé {total_count} ressources de santé correspondant à vos critères"
        }
    
    def _format_response(self, result: Dict[str, Any], interpretation: Dict[str, Any], search_type: str) -> Dict[str, Any]:
        """Format the final response for the frontend"""
        if not result.get("success"):
            return {
                "success": False,
                "results": [],
                "error": result.get("error", "Recherche échouée"),
                "ai_interpretation": interpretation
            }
        
        results = result.get("results", [])
        
        # Determine entity description
        entity_descriptions = {
            "organization": "organisations de santé",
            "practitioner_role": "professionnels de santé",
            "practitioner_name": "professionnels de santé",
            "healthcare_service": "services de santé",
            "device": "équipements médicaux"
        }
        
        entity_type = entity_descriptions.get(search_type, "ressources de santé")
        
        return {
            "success": True,
            "results": results,
            "count": len(results),
            "search_type": search_type,
            "ai_interpretation": interpretation,
            "message": f"Trouvé {len(results)} {entity_type} correspondant à vos critères"
        }
