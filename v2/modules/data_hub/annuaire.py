"""
Annuaire Santé Client for V2 Mediflux
FHIR API client for French healthcare directory
Provides aggregated practitioner and organization data
"""

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
