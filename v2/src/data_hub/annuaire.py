"""
Annuaire Santé Client for V2 Mediflux
FHIR API integration for French healthcare directory
Refactored from V1 smart_orchestrator.py
"""

import asyncio
import requests
import os
from typing import Dict, List, Any, Optional
import logging


class AnnuaireClient:
    """
    Client for Annuaire Santé FHIR API
    Provides practitioner and organization search capabilities
    """
    
    def __init__(self):
        self.api_key = os.getenv("ANNUAIRE_SANTE_API_KEY", "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740")
        self.base_url = "https://gateway.api.esante.gouv.fr/fhir/v1"
        self.timeout = 30
        self.logger = logging.getLogger(__name__)
    
    async def search_practitioners(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search practitioners using FHIR PractitionerRole API
        
        Args:
            params: Search parameters including specialty, location, name, etc.
            
        Returns:
            Dict with search results and metadata
        """
        try:
            # Build FHIR query parameters
            fhir_params = self._build_practitioner_params(params)
            
            # Execute search
            result = await self._search_practitioner_roles(fhir_params)
            
            # Process and enrich results
            if result["success"]:
                result["results"] = await self._enrich_practitioner_results(result["results"])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Practitioner search failed: {str(e)}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    async def search_organizations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search organizations using FHIR Organization API
        
        Args:
            params: Search parameters including name, city, type, etc.
            
        Returns:
            Dict with search results and metadata
        """
        try:
            # Build FHIR query parameters
            fhir_params = self._build_organization_params(params)
            
            # Execute search
            result = await self._search_organizations_api(fhir_params)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Organization search failed: {str(e)}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    def _build_practitioner_params(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Build FHIR parameters for practitioner search"""
        fhir_params = {}
        
        # Specialty/role mapping
        if params.get("specialty"):
            specialty_code = self._map_specialty_to_code(params["specialty"])
            if specialty_code:
                fhir_params["role"] = specialty_code
        
        # Location parameters
        if params.get("location"):
            location = params["location"]
            # Try postal code first
            if location.isdigit() and len(location) == 5:
                fhir_params["address-postalcode"] = location
            else:
                fhir_params["address-city"] = location
        
        # Name search
        if params.get("practitioner_name"):
            fhir_params["name"] = params["practitioner_name"]
        
        # Default parameters
        fhir_params["active"] = "true"
        fhir_params["_count"] = str(params.get("limit", 20))
        
        return fhir_params
    
    def _build_organization_params(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Build FHIR parameters for organization search"""
        fhir_params = {}
        
        # Organization name
        if params.get("organization_name"):
            name = params["organization_name"]
            # Avoid generic terms that cause timeouts
            generic_terms = ["hôpital", "clinique", "centre", "cabinet"]
            if not any(term in name.lower() for term in generic_terms):
                fhir_params["name"] = name
        
        # Location parameters (preferred over name for generic searches)
        if params.get("location"):
            location = params["location"]
            if location.isdigit() and len(location) == 5:
                fhir_params["address-postalcode"] = location
            else:
                fhir_params["address-city"] = location
        
        # Organization type
        if params.get("organization_type"):
            fhir_params["type"] = params["organization_type"]
        
        # Default parameters
        fhir_params["active"] = "true"
        fhir_params["_count"] = str(params.get("limit", 20))
        
        return fhir_params
    
    async def _search_practitioner_roles(self, fhir_params: Dict[str, str]) -> Dict[str, Any]:
        """Execute FHIR PractitionerRole search"""
        def _make_request():
            headers = {
                'ESANTE-API-KEY': self.api_key,
                'Accept': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/PractitionerRole",
                headers=headers,
                params=fhir_params,
                timeout=self.timeout
            )
            return response
        
        response = await asyncio.get_event_loop().run_in_executor(None, _make_request)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "results": []
            }
        
        bundle = response.json()
        practitioners = bundle.get("entry", [])
        
        return {
            "success": True,
            "results": practitioners,
            "total_count": len(practitioners),
            "query_params": fhir_params
        }
    
    async def _search_organizations_api(self, fhir_params: Dict[str, str]) -> Dict[str, Any]:
        """Execute FHIR Organization search"""
        def _make_request():
            headers = {
                'ESANTE-API-KEY': self.api_key,
                'Accept': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/Organization",
                headers=headers,
                params=fhir_params,
                timeout=self.timeout
            )
            return response
        
        response = await asyncio.get_event_loop().run_in_executor(None, _make_request)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "results": []
            }
        
        bundle = response.json()
        organizations = bundle.get("entry", [])
        
        # Process organization results
        processed_results = []
        for entry in organizations:
            org = entry.get("resource", {})
            processed_results.append(self._process_organization(org))
        
        return {
            "success": True,
            "results": processed_results,
            "total_count": len(processed_results),
            "query_params": fhir_params
        }
    
    async def _enrich_practitioner_results(self, raw_results: List[Dict]) -> List[Dict]:
        """Process and enrich practitioner results"""
        enriched_results = []
        
        for entry in raw_results:
            prac_role = entry.get("resource", {})
            
            # Extract practitioner name from extensions
            full_name = self._extract_practitioner_name(prac_role)
            
            # Extract specialty information
            specialty_info = self._extract_specialty_info(prac_role)
            
            # Extract organization info
            organization_info = await self._get_organization_info(prac_role)
            
            # Build enriched result
            enriched_result = {
                "id": prac_role.get("id", ""),
                "name": full_name,
                "specialty": specialty_info["display"],
                "profession_code": specialty_info["code"],
                "active": prac_role.get("active", True),
                "organization": organization_info,
                "rpps_id": self._extract_rpps_id(prac_role),
                "location": organization_info.get("address", {})
            }
            
            enriched_results.append(enriched_result)
        
        return enriched_results
    
    def _extract_practitioner_name(self, prac_role: Dict) -> str:
        """Extract practitioner name from FHIR extensions"""
        for ext in prac_role.get("extension", []):
            if "PractitionerRole-Name" in ext.get("url", ""):
                vh = ext.get("valueHumanName", {})
                family = vh.get("family", "")
                given = vh.get("given", [])
                
                name_parts = []
                if given:
                    name_parts.extend(given)
                if family:
                    name_parts.append(family)
                
                if name_parts:
                    return " ".join(name_parts)
        
        return "Professionnel de santé"
    
    def _extract_specialty_info(self, prac_role: Dict) -> Dict[str, str]:
        """Extract specialty/profession information"""
        code_info = prac_role.get("code", [])
        
        for code_item in code_info:
            coding_list = code_item.get("coding", [])
            for coding in coding_list:
                system = coding.get("system", "")
                if "TRE-G15-ProfessionSante" in system:
                    code = coding.get("code", "Unknown")
                    display = self._map_profession_code_to_display(code)
                    return {"code": code, "display": display}
        
        return {"code": "Unknown", "display": "Professionnel de santé"}
    
    async def _get_organization_info(self, prac_role: Dict) -> Dict[str, Any]:
        """Get organization information for a practitioner"""
        organization_info = prac_role.get("organization")
        if not organization_info:
            return {"name": "Organisation inconnue", "address": {}}
        
        org_ref = organization_info.get("reference", "")
        if org_ref:
            return await self._fetch_organization_details(org_ref)
        
        return {"name": "Organisation inconnue", "address": {}}
    
    async def _fetch_organization_details(self, org_reference: str) -> Dict[str, Any]:
        """Fetch organization details by reference"""
        try:
            def _make_request():
                headers = {
                    'ESANTE-API-KEY': self.api_key,
                    'Accept': 'application/json'
                }
                
                # Extract organization ID from reference
                org_id = org_reference.split("/")[-1]
                url = f"{self.base_url}/Organization/{org_id}"
                
                response = requests.get(url, headers=headers, timeout=self.timeout)
                return response
            
            response = await asyncio.get_event_loop().run_in_executor(None, _make_request)
            
            if response.status_code == 200:
                org_data = response.json()
                return self._process_organization(org_data)
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch organization details: {str(e)}")
        
        return {"name": "Organisation inconnue", "address": {}}
    
    def _process_organization(self, org_data: Dict) -> Dict[str, Any]:
        """Process organization data from FHIR response"""
        name = org_data.get("name", "Organisation inconnue")
        
        # Extract address information
        addresses = org_data.get("address", [])
        address_info = {}
        
        if addresses:
            addr = addresses[0]  # Take first address
            address_parts = []
            
            if addr.get("line"):
                address_parts.extend(addr["line"])
            if addr.get("city"):
                address_parts.append(addr["city"])
            if addr.get("postalCode"):
                address_parts.append(addr["postalCode"])
            
            address_info = {
                "street": " ".join(addr.get("line", [])),
                "city": addr.get("city", ""),
                "postal_code": addr.get("postalCode", ""),
                "full_address": ", ".join(address_parts) if address_parts else "Adresse non disponible"
            }
        
        return {
            "id": org_data.get("id", ""),
            "name": name,
            "address": address_info,
            "active": org_data.get("active", True),
            "type": self._extract_organization_type(org_data)
        }
    
    def _extract_organization_type(self, org_data: Dict) -> str:
        """Extract organization type from FHIR data"""
        types = org_data.get("type", [])
        if types and len(types) > 0:
            coding = types[0].get("coding", [])
            if coding and len(coding) > 0:
                return coding[0].get("display", "Organisation de santé")
        return "Organisation de santé"
    
    def _extract_rpps_id(self, prac_role: Dict) -> str:
        """Extract RPPS ID from practitioner reference"""
        practitioner_ref = prac_role.get("practitioner", {})
        prac_ref = practitioner_ref.get("reference", "")
        return prac_ref.split("/")[-1] if "/" in prac_ref else ""
    
    def _map_specialty_to_code(self, specialty: str) -> Optional[str]:
        """Map specialty name to FHIR profession code"""
        specialty_map = {
            "médecin": "60",
            "kinésithérapeute": "40", 
            "ostéopathe": "50",
            "dentiste": "86",
            "sage-femme": "31",
            "pharmacien": "96",
            "infirmier": "23",
            "cardiologue": "60",  # General médecin code
            "dermatologue": "60",
            "gynécologue": "60"
        }
        
        specialty_lower = specialty.lower()
        for key, code in specialty_map.items():
            if key in specialty_lower:
                return code
        
        return None
    
    def _map_profession_code_to_display(self, code: str) -> str:
        """Map profession code to display name"""
        code_map = {
            "60": "Médecin",
            "40": "Kinésithérapeute", 
            "50": "Ostéopathe",
            "86": "Dentiste",
            "31": "Sage-femme",
            "96": "Pharmacien",
            "23": "Infirmier",
            "54": "Chiropracteur"
        }
        return code_map.get(code, f"Profession {code}")
    
    async def get_aggregated_data(self, region: str = None, specialty: str = None) -> Dict[str, Any]:
        """
        Get aggregated data for care pathway optimization
        This would typically cache and aggregate data from multiple searches
        """
        # This is a placeholder for aggregated data functionality
        # In production, this would query cached/preprocessed data
        return {
            "success": True,
            "region": region,
            "specialty": specialty,
            "aggregated_data": {
                "average_wait_time": "15 days",
                "sector_1_percentage": "75%",
                "average_tariff": "€25",
                "practitioner_density": "High"
            },
            "note": "Aggregated data functionality to be implemented with caching layer"
        }

import asyncio
import requests
from typing import Dict, List, Any, Optional
import logging


class AnnuaireClient:
    """
    Client for Annuaire Santé de la CNAM FHIR API
    Focuses on aggregated data for care pathway optimization
    """
    
    def __init__(self):
        self.base_url = "https://gateway.api.esante.gouv.fr/fhir"
        self.api_key = "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740"  # From V1
        self.timeout = 30
        self.logger = logging.getLogger(__name__)
    
    async def search_practitioners(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search practitioners with aggregation focus
        
        Args:
            params: Search parameters including specialty, location, etc.
            
        Returns:
            Aggregated practitioner data for pathway optimization
        """
        try:
            specialty = params.get("specialty")
            location = params.get("location")
            practitioner_name = params.get("practitioner_name")
            
            if practitioner_name:
                return await self._search_by_name(practitioner_name)
            elif specialty:
                return await self._search_by_specialty(specialty, location)
            else:
                return await self._search_organizations(location)
                
        except Exception as e:
            self.logger.error(f"Practitioner search failed: {str(e)}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    async def _search_by_specialty(self, specialty: str, location: str = None) -> Dict[str, Any]:
        """
        Search practitioners by specialty with geographic filtering
        """
        try:
            # Map specialty names to role codes
            specialty_codes = {
                "cardiologue": "95",
                "dentiste": "86", 
                "kinésithérapeute": "40",
                "médecin": "60",
                "sage-femme": "31",
                "pharmacien": "96",
                "ostéopathe": "50",
                "infirmier": "23"
            }
            
            role_code = specialty_codes.get(specialty.lower(), "60")  # Default to médecin
            
            # Build search parameters
            search_params = {
                "role": role_code,
                "_count": "50"
            }
            
            if location:
                # Try to determine if location is a city or postal code
                if location.isdigit() and len(location) == 5:
                    search_params["address-postalcode"] = location
                else:
                    search_params["address-city"] = location
            
            # Execute search
            response = await self._make_fhir_request("PractitionerRole", search_params)
            
            if not response["success"]:
                return response
            
            # Aggregate results for pathway optimization
            practitioners = response.get("results", [])
            aggregated_data = self._aggregate_practitioner_data(practitioners, specialty, location)
            
            return {
                "success": True,
                "specialty": specialty,
                "location": location,
                "total_found": len(practitioners),
                "aggregated_data": aggregated_data,
                "raw_results": practitioners[:10]  # Return sample for reference
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Specialty search failed: {str(e)}"
            }
    
    async def _search_by_name(self, name: str) -> Dict[str, Any]:
        """
        Search for specific practitioner by name
        """
        try:
            search_params = {
                "name": name,
                "_count": "20"
            }
            
            response = await self._make_fhir_request("Practitioner", search_params)
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Name search failed: {str(e)}"
            }
    
    async def _search_organizations(self, location: str = None) -> Dict[str, Any]:
        """
        Search healthcare organizations
        """
        try:
            search_params = {"_count": "30"}
            
            if location:
                if location.isdigit() and len(location) == 5:
                    search_params["address-postalcode"] = location
                else:
                    search_params["address-city"] = location
            
            response = await self._make_fhir_request("Organization", search_params)
            
            if response["success"]:
                organizations = response.get("results", [])
                aggregated_org_data = self._aggregate_organization_data(organizations, location)
                
                return {
                    "success": True,
                    "location": location,
                    "total_found": len(organizations),
                    "aggregated_data": aggregated_org_data,
                    "raw_results": organizations[:5]
                }
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Organization search failed: {str(e)}"
            }
    
    async def _make_fhir_request(self, resource_type: str, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make FHIR API request with error handling
        """
        def _make_request():
            url = f"{self.base_url}/{resource_type}"
            headers = {
                "Accept": "application/fhir+json",
                "ESANTE-API-KEY": self.api_key
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            return response
        
        try:
            # Run in thread to avoid blocking
            response = await asyncio.get_event_loop().run_in_executor(None, _make_request)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "results": []
                }
            
            fhir_data = response.json()
            
            # Extract entries from FHIR Bundle
            entries = fhir_data.get("entry", [])
            results = [entry.get("resource", {}) for entry in entries]
            
            return {
                "success": True,
                "results": results,
                "total": fhir_data.get("total", len(results))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "results": []
            }
    
    def _aggregate_practitioner_data(self, practitioners: List[Dict], specialty: str, location: str) -> Dict[str, Any]:
        """
        Aggregate practitioner data for pathway optimization
        """
        if not practitioners:
            return {"error": "No practitioners found for aggregation"}
        
        aggregation = {
            "specialty": specialty,
            "location": location,
            "total_practitioners": len(practitioners),
            "availability_estimate": "medium",  # Would calculate from real data
            "average_wait_time": "2-3 weeks",   # Would calculate from real data
            "sector_distribution": {
                "secteur_1": 0,
                "secteur_2": 0,
                "unknown": len(practitioners)  # Would parse from FHIR data
            },
            "geographic_distribution": {},
            "cost_guidance": {
                "typical_consultation_fee": "€25-30" if specialty == "médecin" else "€30-50",
                "sector_1_available": True,
                "recommendation": f"Secteur 1 {specialty} available in {location or 'this area'}"
            }
        }
        
        # Analyze geographic distribution
        cities = {}
        for practitioner in practitioners:
            # Would extract city from FHIR address data
            city = "Unknown"  # Placeholder
            cities[city] = cities.get(city, 0) + 1
        
        aggregation["geographic_distribution"] = cities
        
        return aggregation
    
    def _aggregate_organization_data(self, organizations: List[Dict], location: str) -> Dict[str, Any]:
        """
        Aggregate organization data for pathway optimization
        """
        if not organizations:
            return {"error": "No organizations found for aggregation"}
        
        # Categorize organizations by type
        org_types = {}
        for org in organizations:
            org_type = org.get("type", [{}])[0].get("text", "Unknown")
            org_types[org_type] = org_types.get(org_type, 0) + 1
        
        return {
            "location": location,
            "total_organizations": len(organizations),
            "organization_types": org_types,
            "public_hospitals_available": "Hôpital" in str(org_types),
            "private_clinics_available": "Clinique" in str(org_types),
            "accessibility_score": "good",  # Would calculate from real data
            "cost_guidance": {
                "public_options_available": True,
                "private_options_available": True,
                "recommendation": "Mix of public and private facilities available"
            }
        }
    
    async def get_tariff_analysis(self, specialty: str, location: str) -> Dict[str, Any]:
        """
        Get tariff analysis for a specialty in a location
        TODO: Implement with real tariff data parsing
        """
        return {
            "specialty": specialty,
            "location": location,
            "average_secteur_1_tariff": "€25-30",
            "average_secteur_2_tariff": "€35-50",
            "secteur_1_availability": "high",
            "cost_optimization_tip": f"Choose Secteur 1 {specialty} to minimize costs",
            "data_freshness": "estimated"  # Would be "current" with real data
        }
