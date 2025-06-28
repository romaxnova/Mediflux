"""
Medication Search Toolkit for API-BDPM Integration
Provides medication search capabilities using the French public medication database
"""

import requests
import json
from typing import Dict, List, Any, Optional
import traceback


class MedicationToolkit:
    """
    Toolkit for searching French medications using API-BDPM GraphQL
    """
    
    def __init__(self):
        self.api_url = "https://api-bdpm-graphql.axel-op.fr/graphql"
        self.timeout = 30
    
    def search_by_name(self, name: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search medications by name/denomination
        
        Args:
            name: Medication name to search for
            limit: Maximum number of results to return
            
        Returns:
            Dict with success status, results, and metadata
        """
        try:
            print(f"[MEDICATION_DEBUG] Searching medications by name: '{name}'")
            
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
            
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
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
            
            medications = data.get("data", {}).get("medicaments", [])
            
            # Format results for frontend
            formatted_results = []
            for med in medications:
                formatted_med = self._format_medication_result(med)
                formatted_results.append(formatted_med)
            
            print(f"[MEDICATION_DEBUG] Found {len(formatted_results)} medications")
            
            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "search_type": "medication_name"
            }
            
        except Exception as e:
            print(f"[MEDICATION_ERROR] Name search failed: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def search_by_substance(self, substance: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search medications by active substance
        
        Args:
            substance: Active substance name to search for
            limit: Maximum number of results to return
            
        Returns:
            Dict with success status, results, and metadata
        """
        try:
            print(f"[MEDICATION_DEBUG] Searching medications by substance: '{substance}'")
            
            query = """
            query SearchMedicationsBySubstance($substance: StringFilter!, $limit: Int) {
                substances(denomination: $substance, limit: 10) {
                    code_substance
                    denominations
                    medicaments(limit: $limit) {
                        CIS
                        denomination
                        forme_pharmaceutique
                        voies_administration
                        statut_admin_AMM
                        etat_commercialisation
                        date_AMM
                        surveillance_renforcee
                        substances {
                            code_substance
                            denominations
                            dosage_substance
                            reference_dosage
                            nature_composant
                        }
                        presentations {
                            CIP7
                            libelle
                            taux_remboursement
                            prix_sans_honoraires
                            prix_avec_honoraires
                            agrement_collectivites
                        }
                    }
                }
            }
            """
            
            variables = {
                "substance": {"contains_one_of": [substance.lower()]},
                "limit": limit
            }
            
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
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
            
            substances = data.get("data", {}).get("substances", [])
            
            # Flatten medications from all matching substances
            all_medications = []
            for substance_data in substances:
                medications = substance_data.get("medicaments", [])
                for med in medications:
                    # Add substance context
                    med["matched_substance"] = {
                        "code": substance_data.get("code_substance"),
                        "names": substance_data.get("denominations", [])
                    }
                    all_medications.append(med)
            
            # Format results for frontend
            formatted_results = []
            for med in all_medications:
                formatted_med = self._format_medication_result(med)
                formatted_results.append(formatted_med)
            
            print(f"[MEDICATION_DEBUG] Found {len(formatted_results)} medications by substance")
            
            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "search_type": "medication_substance"
            }
            
        except Exception as e:
            print(f"[MEDICATION_ERROR] Substance search failed: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_medication_details(self, cis_code: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific medication by CIS code
        
        Args:
            cis_code: CIS (Code Identifiant de Spécialité) of the medication
            
        Returns:
            Dict with detailed medication information
        """
        try:
            print(f"[MEDICATION_DEBUG] Getting details for CIS: {cis_code}")
            
            query = """
            query GetMedicationDetails($cis: [ID!]) {
                medicaments(CIS: $cis) {
                    CIS
                    denomination
                    forme_pharmaceutique
                    voies_administration
                    statut_admin_AMM
                    type_procedure_AMM
                    etat_commercialisation
                    date_AMM
                    surveillance_renforcee
                    conditions_prescription
                    titulaires
                    numero_autorisation_europeenne
                    statut_BDM
                    substances {
                        code_substance
                        denominations
                        dosage_substance
                        reference_dosage
                        nature_composant
                        designation_element_pharmaceutique
                    }
                    presentations {
                        CIP7
                        CIP13
                        libelle
                        statut_admin
                        etat_commercialisation
                        date_declaration_commercialisation
                        agrement_collectivites
                        taux_remboursement
                        prix_sans_honoraires
                        prix_avec_honoraires
                        honoraires
                        indications_remboursement
                    }
                    groupes_generiques {
                        id
                        libelle
                        princeps {
                            CIS
                            denomination
                        }
                        generiques {
                            CIS
                            denomination
                        }
                    }
                }
            }
            """
            
            variables = {"cis": [cis_code]}
            
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
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
            
            medications = data.get("data", {}).get("medicaments", [])
            
            if not medications:
                return {
                    "success": False,
                    "error": f"No medication found with CIS: {cis_code}",
                    "results": []
                }
            
            # Format the detailed result
            detailed_med = self._format_detailed_medication(medications[0])
            
            return {
                "success": True,
                "results": [detailed_med],
                "count": 1,
                "search_type": "medication_details"
            }
            
        except Exception as e:
            print(f"[MEDICATION_ERROR] Details fetch failed: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _format_medication_result(self, med: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format medication data for consistent frontend display
        """
        # Get primary substance
        primary_substance = None
        substances = med.get("substances", [])
        if substances:
            primary_substance = substances[0]
        
        # Get main presentation (first one with price if available)
        main_presentation = None
        presentations = med.get("presentations", [])
        if presentations:
            # Prefer presentations with price information
            priced_presentations = [p for p in presentations if p.get("prix_sans_honoraires")]
            main_presentation = priced_presentations[0] if priced_presentations else presentations[0]
        
        # Determine reimbursement status
        reimbursement_status = "Non remboursé"
        if main_presentation and main_presentation.get("taux_remboursement"):
            reimbursement_status = f"{main_presentation['taux_remboursement']}%"
        
        return {
            "id": med.get("CIS", ""),
            "name": med.get("denomination", "Médicament inconnu"),
            "cis_code": med.get("CIS", ""),
            "pharmaceutical_form": med.get("forme_pharmaceutique", "Forme inconnue"),
            "administration_route": med.get("voies_administration", "Voie inconnue"),
            "marketing_status": med.get("etat_commercialisation", "Statut inconnu"),
            "amm_status": med.get("statut_admin_AMM", "Statut AMM inconnu"),
            "amm_date": med.get("date_AMM", "Date inconnue"),
            "enhanced_surveillance": med.get("surveillance_renforcee", False),
            "prescription_conditions": med.get("conditions_prescription", []),
            "holders": med.get("titulaires", []),
            "primary_substance": {
                "code": primary_substance.get("code_substance", "") if primary_substance else "",
                "names": primary_substance.get("denominations", []) if primary_substance else [],
                "dosage": primary_substance.get("dosage_substance", "") if primary_substance else "",
                "reference": primary_substance.get("reference_dosage", "") if primary_substance else "",
            } if primary_substance else None,
            "all_substances": substances,
            "main_presentation": {
                "cip7": main_presentation.get("CIP7", "") if main_presentation else "",
                "cip13": main_presentation.get("CIP13", "") if main_presentation else "",
                "label": main_presentation.get("libelle", "") if main_presentation else "",
                "reimbursement_rate": main_presentation.get("taux_remboursement") if main_presentation else None,
                "price_without_fees": main_presentation.get("prix_sans_honoraires") if main_presentation else None,
                "price_with_fees": main_presentation.get("prix_avec_honoraires") if main_presentation else None,
                "collective_agreement": main_presentation.get("agrement_collectivites") if main_presentation else None,
            } if main_presentation else None,
            "all_presentations": presentations,
            "reimbursement_status": reimbursement_status,
            "resource_type": "medication",
            "search_metadata": {
                "matched_substance": med.get("matched_substance"),  # Only for substance searches
                "presentation_count": len(presentations),
                "substance_count": len(substances)
            }
        }
    
    def _format_detailed_medication(self, med: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format detailed medication data with all available information
        """
        base_format = self._format_medication_result(med)
        
        # Add detailed information
        base_format.update({
            "detailed_info": {
                "authorization_procedure": med.get("type_procedure_AMM", ""),
                "european_authorization_number": med.get("numero_autorisation_europeenne", ""),
                "bdm_status": med.get("statut_BDM", ""),
                "generic_groups": med.get("groupes_generiques", []),
                "complete_presentations": med.get("presentations", []),
                "complete_substances": med.get("substances", [])
            }
        })
        
        return base_format
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return toolkit capabilities for orchestrator registration
        """
        return {
            "intents": ["find_medication", "search_medication", "medication_info", "drug_search"],
            "entities": ["medication_name", "substance_name", "cis_code"],
            "search_types": ["name", "substance", "details"],
            "confidence_threshold": 0.7,
            "supported_languages": ["french", "english"],
            "data_source": "ANSM - Agence nationale de sécurité du médicament",
            "api_endpoint": self.api_url
        }


# Test functions for development
def test_medication_search():
    """Test function for medication search"""
    toolkit = MedicationToolkit()
    
    print("Testing medication name search...")
    result = toolkit.search_by_name("Doliprane", limit=3)
    print(f"Name search result: {result['success']}, count: {result.get('count', 0)}")
    
    print("\nTesting substance search...")
    result = toolkit.search_by_substance("Paracetamol", limit=3)
    print(f"Substance search result: {result['success']}, count: {result.get('count', 0)}")
    
    print("\nTesting CIS details...")
    result = toolkit.get_medication_details("62204255")
    print(f"Details search result: {result['success']}, count: {result.get('count', 0)}")


if __name__ == "__main__":
    test_medication_search()
