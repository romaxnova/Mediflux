"""
Odissé API Client for V2 Mediflux
Enhanced implementation for healthcare data integration
Focus on professional densities, appointment delays, and access indicators
"""

import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime


class OdisseClient:
    """
    Enhanced client for Odissé API (Santé Publique France)
    Provides healthcare access indicators and professional density data
    """
    
    def __init__(self):
        self.base_url = "https://odisse.santepubliquefrance.fr/api/explore/v2.1"
        self.session = None
        self.logger = logging.getLogger(__name__)
        
        # Target datasets for healthcare analysis
        self.datasets = {
            "densities": "densites_professionnels_sante",
            "delays": "delais_rendezvous_specialistes", 
            "access_indicators": "indicateurs_acces_soins"
        }
    
    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _make_api_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with comprehensive error handling"""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"success": True, "data": data}
                elif response.status == 404:
                    return {"success": False, "error": "Dataset not found"}
                elif response.status == 429:
                    return {"success": False, "error": "Rate limit exceeded"}
                else:
                    error_text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                    
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    async def get_professional_densities(self, location: str = None, specialty: str = None) -> Dict[str, Any]:
        """Get healthcare professional density data"""
        try:
            params = {"dataset": self.datasets["densities"], "limit": 50}
            
            # Build location filter
            if location:
                params["where"] = f"region like '{location}%' or departement like '{location}%'"
            
            # Add specialty filter
            if specialty:
                specialty_filter = f"profession like '{specialty}%'"
                if "where" in params:
                    params["where"] += f" and {specialty_filter}"
                else:
                    params["where"] = specialty_filter
            
            result = await self._make_api_request("catalog/datasets", params)
            
            if result["success"]:
                return {
                    "success": True,
                    "location": location,
                    "specialty": specialty,
                    "density_data": result["data"],
                    "query_timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Professional density query failed: {str(e)}"}
    
    async def get_appointment_delays(self, specialty: str, location: str = None) -> Dict[str, Any]:
        """Get appointment delay data for medical specialties"""
        try:
            params = {"dataset": self.datasets["delays"], "limit": 50}
            
            # Specialty filter (required)
            where_filters = [f"specialite like '{specialty}%'"]
            
            # Location filter (optional)
            if location:
                where_filters.append(f"(region like '{location}%' or ville like '{location}%')")
            
            params["where"] = " and ".join(where_filters)
            
            result = await self._make_api_request("catalog/datasets", params)
            
            if result["success"]:
                return {
                    "success": True,
                    "specialty": specialty,
                    "location": location,
                    "delay_data": result["data"],
                    "query_timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Appointment delay query failed: {str(e)}"}
    
    async def get_access_indicators(self, location: str) -> Dict[str, Any]:
        """Get healthcare access indicators for location"""
        try:
            params = {
                "dataset": self.datasets["access_indicators"], 
                "limit": 100,
                "where": f"territoire like '{location}%' or region like '{location}%'"
            }
            
            result = await self._make_api_request("catalog/datasets", params)
            
            if result["success"]:
                return {
                    "success": True,
                    "location": location,
                    "access_data": result["data"],
                    "query_timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Access indicators query failed: {str(e)}"}
    
    async def get_comprehensive_data(self, location: str, specialty: str = None) -> Dict[str, Any]:
        """Get comprehensive healthcare access data for care pathway analysis"""
        try:
            results = {}
            errors = []
            
            # Professional densities
            density_result = await self.get_professional_densities(location, specialty)
            results["professional_densities"] = density_result
            if not density_result["success"]:
                errors.append(f"Densities: {density_result['error']}")
            
            # Appointment delays (if specialty specified)
            if specialty:
                delay_result = await self.get_appointment_delays(specialty, location)
                results["appointment_delays"] = delay_result
                if not delay_result["success"]:
                    errors.append(f"Delays: {delay_result['error']}")
            
            # Access indicators
            access_result = await self.get_access_indicators(location)
            results["access_indicators"] = access_result
            if not access_result["success"]:
                errors.append(f"Access: {access_result['error']}")
            
            # Calculate success metrics
            successful = sum(1 for r in results.values() if r.get("success", False))
            total = len(results)
            
            return {
                "success": successful > 0,
                "location": location,
                "specialty": specialty,
                "data_completeness": f"{successful}/{total}",
                "results": results,
                "errors": errors if errors else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": f"Comprehensive query failed: {str(e)}"}
    
    def get_datasets_info(self) -> Dict[str, str]:
        """Get information about available datasets"""
        return {
            "densities": "Healthcare professional densities by region/specialty",
            "delays": "Appointment delays by specialty and location", 
            "access_indicators": "General healthcare access indicators by region"
        }
    
    async def close(self):
        """Clean up HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
