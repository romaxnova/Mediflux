#!/usr/bin/env python3
"""
Test script for SAE (hospital statistics) data integration
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_hub.sae import SAEClient, get_hospital_recommendations

async def test_sae_integration():
    """Test SAE data processing and queries"""
    print("🏥 Testing SAE Hospital Statistics Integration")
    print("=" * 50)
    
    client = SAEClient()
    
    # Process all SAE data
    print("📊 Processing SAE data...")
    results = await client.process_all_sae_data()
    
    print(f"✅ Processed:")
    print(f"   - {results['hospitals']} hospitals")
    print(f"   - {results['mco_activity']} MCO activity records")
    print(f"   - {results['emergency_services']} emergency services")
    print(f"   - {results['regional_metrics']} regional metrics")
    
    # Test hospital capacity queries
    print("\n🔍 Testing hospital capacity queries...")
    
    # Get hospitals with low occupancy (more availability)
    available_hospitals = await client.get_low_capacity_hospitals(max_occupancy=0.7)
    print(f"Found {len(available_hospitals)} hospitals with <70% occupancy")
    
    if available_hospitals:
        print("\nTop 5 most available hospitals:")
        for i, hospital in enumerate(available_hospitals[:5], 1):
            print(f"{i}. {hospital['name']} ({hospital['city']}, {hospital['department']})")
            print(f"   - {hospital['beds']} beds, {hospital['occupancy_rate']:.1%} occupancy")
            print(f"   - Availability score: {hospital['availability_score']}%")
    
    # Test regional queries
    print("\n🌍 Testing regional analysis...")
    
    # Paris region (75)
    paris_hospitals = await client.get_hospital_capacity_by_region(department="75")
    print(f"Found {len(paris_hospitals)} hospitals in Paris (75)")
    
    # Lyon region (69) 
    lyon_hospitals = await client.get_hospital_capacity_by_region(department="69")
    print(f"Found {len(lyon_hospitals)} hospitals in Lyon (69)")
    
    # Test recommendation system
    print("\n💡 Testing recommendation system...")
    
    recommendations = await get_hospital_recommendations("75000", specialty="cardiology")
    print(f"Generated {len(recommendations)} recommendations for Paris cardiology")
    
    if recommendations:
        print("\nTop 3 recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec['name']} ({rec['city']})")
            print(f"   - {rec['recommendation_reason']}")
            print(f"   - Est. {rec['beds_available_estimate']} beds available")
    
    print("\n✅ SAE integration test completed successfully!")
    return results

if __name__ == "__main__":
    asyncio.run(test_sae_integration())
