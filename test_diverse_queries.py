#!/usr/bin/env python3
"""
Diverse Test Queries for Mediflux Healthcare Chat Interface
==========================================================

This script tests the AI-powered healthcare search system with a wide variety
of realistic queries in both French and English, covering different:
- Healthcare specialties
- Geographic locations  
- Query types (organization vs practitioner)
- Languages and phrasing styles
"""

import requests
import json
import time
from typing import List, Dict

# Test queries organized by category
DIVERSE_TEST_QUERIES = {
    "specialists_french": [
        "je cherche un cardiologue à Lyon",
        "trouve-moi un dermatologue à Nice", 
        "où trouver un neurologue à Bordeaux",
        "je veux consulter un psychiatre à Strasbourg",
        "il me faut un orthopédiste à Lille"
    ],
    
    "specialists_english": [
        "find an ophthalmologist in Toulouse",
        "I need a radiologist in Nantes",
        "looking for an ENT doctor in Montpellier",
        "find me a pediatrician in Rennes",
        "search for an endocrinologist in Grenoble"
    ],
    
    "organizations_french": [
        "je cherche une pharmacie à Marseille",
        "trouve un laboratoire d'analyses à Cannes",
        "où est la clinique la plus proche de Annecy",
        "centres de radiologie à Reims",
        "maisons de santé pluridisciplinaires à Tours"
    ],
    
    "organizations_english": [
        "find hospitals in Nancy",
        "medical centers near Perpignan",
        "imaging centers in Poitiers",
        "rehabilitation clinics in Clermont-Ferrand",
        "dental clinics in Brest"
    ],
    
    "paris_specific": [
        "hôpitaux dans le 15e arrondissement",
        "cliniques privées dans le 16e", 
        "pharmacies ouvertes 7e arrondissement",
        "find specialists in 8th arrondissement",
        "medical centers in Montmartre"
    ],
    
    "complex_queries": [
        "je cherche un médecin généraliste qui parle anglais à Aix-en-Provence",
        "centre médical avec urgences pédiatriques à Mulhouse",
        "find a sports medicine clinic near Chamonix",
        "laboratoires ouverts le weekend à Avignon",
        "consultations sans rendez-vous à Saint-Étienne"
    ],
    
    "regional_cities": [
        "médecins à La Rochelle",
        "pharmacies à Rouen", 
        "hôpitaux à Metz",
        "cliniques à Dijon",
        "centres de santé à Orléans"
    ]
}

def test_query(query: str, endpoint: str = "http://localhost:9000/mcp/execute") -> Dict:
    """Test a single query and return the response"""
    try:
        response = requests.post(
            endpoint,
            json={"prompt": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "query": query,
                "status": "success",
                "response": response.json(),
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "query": query,
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
            
    except requests.exceptions.Timeout:
        return {
            "query": query,
            "status": "timeout",
            "error": "Request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "query": query,
            "status": "error", 
            "error": str(e)
        }

def run_test_suite():
    """Run the complete test suite with diverse queries"""
    print("🏥 Mediflux Diverse Query Test Suite")
    print("=" * 50)
    
    results = []
    total_queries = 0
    
    for category, queries in DIVERSE_TEST_QUERIES.items():
        print(f"\n📋 Testing Category: {category.upper().replace('_', ' ')}")
        print("-" * 40)
        
        for query in queries:
            total_queries += 1
            print(f"🔍 Query {total_queries}: {query}")
            
            result = test_query(query)
            results.append(result)
            
            if result["status"] == "success":
                data = result["response"]["choices"][0]["data"]["structured_data"]["data"]
                result_count = len(data.get("results", []))
                query_type = data.get("query_type", "unknown")
                confidence = data.get("search_metadata", {}).get("confidence", 0)
                
                print(f"   ✅ Success: {result_count} results ({query_type}, confidence: {confidence})")
                print(f"   ⏱️  Response time: {result['response_time']:.2f}s")
                
                # Show first result as example
                if result_count > 0:
                    first_result = data["results"][0]
                    name = first_result.get("name", "N/A")
                    city = first_result.get("address", {}).get("city", "N/A")
                    print(f"   📌 Example: {name} in {city}")
                    
            elif result["status"] == "timeout":
                print(f"   ⏰ Timeout: {result['error']}")
            else:
                print(f"   ❌ Error: {result['error']}")
            
            # Small delay between requests
            time.sleep(1)
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    
    successful = len([r for r in results if r["status"] == "success"])
    timeouts = len([r for r in results if r["status"] == "timeout"])
    errors = len([r for r in results if r["status"] == "error"])
    
    print(f"Total Queries: {total_queries}")
    print(f"✅ Successful: {successful} ({successful/total_queries*100:.1f}%)")
    print(f"⏰ Timeouts: {timeouts} ({timeouts/total_queries*100:.1f}%)")
    print(f"❌ Errors: {errors} ({errors/total_queries*100:.1f}%)")
    
    # Average response time for successful queries
    successful_times = [r["response_time"] for r in results if r["status"] == "success"]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"⏱️  Average Response Time: {avg_time:.2f}s")
    
    return results

def quick_test():
    """Run a quick test with just a few diverse queries"""
    quick_queries = [
        "je cherche une pharmacie à Marseille",  # French pharmacy
        "find a cardiologist in Lyon",           # English specialist  
        "hôpitaux dans le 16e arrondissement",   # Paris arrondissement
        "centres médicaux à Toulouse",           # French medical centers
        "dental clinics in Nice"                 # English dental
    ]
    
    print("🚀 Quick Diverse Test")
    print("=" * 30)
    
    for i, query in enumerate(quick_queries, 1):
        print(f"\n{i}. Testing: {query}")
        result = test_query(query)
        
        if result["status"] == "success":
            data = result["response"]["choices"][0]["data"]["structured_data"]["data"]
            count = len(data.get("results", []))
            query_type = data.get("query_type", "unknown")
            print(f"   ✅ {count} results ({query_type}) in {result['response_time']:.1f}s")
        else:
            print(f"   ❌ {result['status']}: {result.get('error', 'Unknown error')}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        run_test_suite()
