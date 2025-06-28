#!/usr/bin/env python3
"""
Test script for medication toolkit
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
                    substances {
                        code_substance
                        denominations
                        dosage_substance
                        reference_dosage
                    }
                    presentations {
                        CIP7
                        libelle
                        taux_remboursement
                        prix_sans_honoraires
                        prix_avec_honoraires
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
            
            print(f"[MEDICATION_DEBUG] API response status: {response.status_code}")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "results": []
                }
            
            data = response.json()
            print(f"[MEDICATION_DEBUG] API response data keys: {list(data.keys())}")
            
            if "errors" in data:
                return {
                    "success": False,
                    "error": f"GraphQL errors: {data['errors']}",
                    "results": []
                }
            
            medications = data.get("data", {}).get("medicaments", [])
            print(f"[MEDICATION_DEBUG] Found {len(medications)} raw medications")
            
            # Simple formatting for now
            formatted_results = []
            for med in medications:
                formatted_med = {
                    "id": med.get("CIS", ""),
                    "name": med.get("denomination", "Unknown medication"),
                    "cis_code": med.get("CIS", ""),
                    "pharmaceutical_form": med.get("forme_pharmaceutique", "Unknown form"),
                    "administration_route": med.get("voies_administration", "Unknown route"),
                    "marketing_status": med.get("etat_commercialisation", "Unknown status"),
                    "resource_type": "medication"
                }
                formatted_results.append(formatted_med)
            
            print(f"[MEDICATION_DEBUG] Formatted {len(formatted_results)} medications")
            
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


def test_medication_search():
    """Test function for medication search"""
    print("=== Testing Medication Toolkit ===")
    
    toolkit = MedicationToolkit()
    
    print("\n1. Testing Doliprane search...")
    result = toolkit.search_by_name("Doliprane", limit=3)
    print(f"✅ Success: {result['success']}")
    print(f"✅ Count: {result.get('count', 0)}")
    
    if result['success'] and result['results']:
        first = result['results'][0]
        print(f"✅ First result: {first['name']}")
        print(f"   CIS: {first['cis_code']}")
        print(f"   Form: {first['pharmaceutical_form']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    print("\n2. Testing Aspirin search...")
    result = toolkit.search_by_name("Aspirin", limit=2)
    print(f"✅ Success: {result['success']}")
    print(f"✅ Count: {result.get('count', 0)}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_medication_search()
