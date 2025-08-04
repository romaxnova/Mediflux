"""
BDPM Client for V2 Mediflux
Refactored medication search toolkit using French public medication database
Optimized for reimbursement simulation and cost analysis
"""

import requests
import json
import asyncio
from typing import Dict, List, Any, Optional
import logging


class BDPMClient:
    """
    Client for API-BDPM GraphQL - French public medication database
    Provides medication search and reimbursement information
    """
    
    def __init__(self):
        self.api_url = "https://api-bdpm-graphql.axel-op.fr/graphql"
        self.timeout = 30
        self.logger = logging.getLogger(__name__)
    
    async def search_medication(self, query: str, search_type: str = "name", limit: int = 10) -> Dict[str, Any]:
        """
        Search medications by name, substance, or CIS code
        
        Args:
            query: Search term (medication name, substance, or CIS code)
            search_type: "name", "substance", or "cis_code"
            limit: Maximum number of results
            
        Returns:
            Dict with search results and metadata
        """
        try:
            if search_type == "name":
                return await self._search_by_name(query, limit)
            elif search_type == "substance":
                return await self._search_by_substance(query, limit)
            elif search_type == "cis_code":
                return await self._search_by_cis_code(query)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported search type: {search_type}",
                    "results": []
                }
                
        except Exception as e:
            self.logger.error(f"BDPM search failed: {str(e)}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    async def _search_by_name(self, name: str, limit: int) -> Dict[str, Any]:
        """Search medications by name/denomination"""
        query = """
        query SearchMedicationsByName($name: StringFilter!, $limit: Int) {
            medicaments(denomination: $name, limit: $limit) {
                CIS
                denomination
                forme_pharmaceutique
                voies_administration
                statut_admin_AMM
                etat_commercialisation
                date_AMM
                surveillance_renforcee
                conditions_prescription
                titulaires
                substances {
                    code_substance
                    denominations
                    dosage_substance
                    reference_dosage
                    nature_composant
                }
                presentations {
                    CIP7
                    CIP13
                    libelle
                    taux_remboursement
                    prix_sans_honoraires
                    prix_avec_honoraires
                    agrement_collectivites
                    indications_remboursement
                }
            }
        }
        """
        
        variables = {
            "name": {"contains_one_of": [name.lower()]},
            "limit": limit
        }
        
        return await self._execute_graphql_query(query, variables, "medicaments")
    
    async def _search_by_substance(self, substance: str, limit: int) -> Dict[str, Any]:
        """Search medications by active substance"""
        query = """
        query SearchBySubstance($substance: StringFilter!, $limit: Int) {
            substances(denominations: $substance, limit: $limit) {
                code_substance
                denominations
                medicaments {
                    CIS
                    denomination
                    forme_pharmaceutique
                    voies_administration
                    etat_commercialisation
                    presentations {
                        CIP7
                        CIP13
                        libelle
                        taux_remboursement
                        prix_sans_honoraires
                        prix_avec_honoraires
                        indications_remboursement
                    }
                }
            }
        }
        """
        
        variables = {
            "substance": {"contains_one_of": [substance.lower()]},
            "limit": limit
        }
        
        result = await self._execute_graphql_query(query, variables, "substances")
        
        # Flatten results - extract medications from substances
        if result["success"] and result["results"]:
            medications = []
            for substance_item in result["results"]:
                for med in substance_item.get("medicaments", []):
                    med["matched_substance"] = {
                        "code": substance_item["code_substance"],
                        "names": substance_item["denominations"]
                    }
                    medications.append(med)
            
            result["results"] = medications
            result["total_substances"] = len(result["results"])
        
        return result
    
    async def _search_by_cis_code(self, cis_code: str) -> Dict[str, Any]:
        """Search medication by specific CIS code"""
        query = """
        query SearchByCIS($cis: String!) {
            medicament(CIS: $cis) {
                CIS
                denomination
                forme_pharmaceutique
                voies_administration
                statut_admin_AMM
                etat_commercialisation
                date_AMM
                surveillance_renforcee
                conditions_prescription
                titulaires
                substances {
                    code_substance
                    denominations
                    dosage_substance
                    reference_dosage
                    nature_composant
                }
                presentations {
                    CIP7
                    CIP13
                    libelle
                    taux_remboursement
                    prix_sans_honoraires
                    prix_avec_honoraires
                    agrement_collectivites
                    indications_remboursement
                }
            }
        }
        """
        
        variables = {"cis": cis_code}
        
        result = await self._execute_graphql_query(query, variables, "medicament")
        
        # Convert single result to list format for consistency
        if result["success"] and result["results"]:
            result["results"] = [result["results"]]
        
        return result
    
    async def _execute_graphql_query(self, query: str, variables: Dict[str, Any], result_key: str) -> Dict[str, Any]:
        """Execute GraphQL query with error handling"""
        def _make_request():
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            return response
        
        # Run request in thread to avoid blocking
        response = await asyncio.get_event_loop().run_in_executor(None, _make_request)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API error: {response.status_code}",
                "results": []
            }
        
        data = response.json()
        
        if "errors" in data:
            return {
                "success": False,
                "error": f"GraphQL errors: {data['errors']}",
                "results": []
            }
        
        results = data.get("data", {}).get(result_key, [])
        if results is None:
            results = []
        
        return {
            "success": True,
            "results": results,
            "total_count": len(results) if isinstance(results, list) else (1 if results else 0),
            "query_info": {
                "search_term": variables,
                "result_type": result_key
            }
        }
    
    async def get_reimbursement_info(self, cip_code: str) -> Dict[str, Any]:
        """
        Get detailed reimbursement information for a specific presentation
        """
        try:
            query = """
            query GetPresentationInfo($cip: String!) {
                presentation(CIP13: $cip) {
                    CIP7
                    CIP13
                    libelle
                    taux_remboursement
                    prix_sans_honoraires
                    prix_avec_honoraires
                    agrement_collectivites
                    indications_remboursement
                    medicament {
                        CIS
                        denomination
                        forme_pharmaceutique
                        etat_commercialisation
                    }
                }
            }
            """
            
            variables = {"cip": cip_code}
            result = await self._execute_graphql_query(query, variables, "presentation")
            
            if result["success"] and result["results"]:
                presentation = result["results"]
                
                # Calculate reimbursement details
                reimbursement_details = self._calculate_reimbursement_details(presentation)
                
                return {
                    "success": True,
                    "presentation": presentation,
                    "reimbursement_analysis": reimbursement_details
                }
            else:
                return {
                    "success": False,
                    "error": "Presentation not found or no reimbursement data available"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Reimbursement info query failed: {str(e)}"
            }
    
    def _calculate_reimbursement_details(self, presentation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate detailed reimbursement breakdown
        """
        try:
            prix_sans_honoraires = presentation.get("prix_sans_honoraires")
            prix_avec_honoraires = presentation.get("prix_avec_honoraires")
            taux_remboursement = presentation.get("taux_remboursement")
            
            if not all([prix_sans_honoraires, taux_remboursement]):
                return {"error": "Insufficient pricing data for calculation"}
            
            # Convert percentage to decimal
            if isinstance(taux_remboursement, str):
                taux_decimal = float(taux_remboursement.rstrip('%')) / 100
            else:
                taux_decimal = float(taux_remboursement) / 100
            
            # Calculate reimbursement amounts
            base_price = float(prix_sans_honoraires) if prix_sans_honoraires else 0
            total_price = float(prix_avec_honoraires) if prix_avec_honoraires else base_price
            
            secu_reimbursement = base_price * taux_decimal
            patient_remainder = total_price - secu_reimbursement
            
            return {
                "base_price_euros": base_price,
                "total_price_euros": total_price,
                "secu_reimbursement_rate": f"{taux_decimal * 100:.0f}%",
                "secu_reimbursement_euros": round(secu_reimbursement, 2),
                "patient_remainder_euros": round(patient_remainder, 2),
                "honoraires_euros": round(total_price - base_price, 2) if prix_avec_honoraires else 0,
                "is_reimbursed": taux_decimal > 0,
                "reimbursement_conditions": presentation.get("indications_remboursement", "None specified")
            }
            
        except (ValueError, TypeError) as e:
            return {"error": f"Calculation error: {str(e)}"}
    
    async def search_generics(self, medication_name: str) -> Dict[str, Any]:
        """
        Find generic alternatives for a medication
        """
        try:
            # First search for the original medication
            original_result = await self.search_medication(medication_name, "name", 1)
            
            if not original_result["success"] or not original_result["results"]:
                return {
                    "success": False,
                    "error": "Original medication not found"
                }
            
            original_med = original_result["results"][0]
            
            # Extract active substances
            substances = original_med.get("substances", [])
            if not substances:
                return {
                    "success": False,
                    "error": "No active substances found for generic search"
                }
            
            # Search for medications with the same substances
            generics = []
            for substance in substances:
                for substance_name in substance.get("denominations", []):
                    substance_result = await self._search_by_substance(substance_name, 20)
                    if substance_result["success"]:
                        generics.extend(substance_result["results"])
            
            # Filter out the original medication and duplicates
            original_cis = original_med.get("CIS")
            unique_generics = {}
            
            for generic in generics:
                cis = generic.get("CIS")
                if cis and cis != original_cis:
                    unique_generics[cis] = generic
            
            return {
                "success": True,
                "original_medication": original_med,
                "generic_alternatives": list(unique_generics.values()),
                "total_generics_found": len(unique_generics)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Generic search failed: {str(e)}"
            }
