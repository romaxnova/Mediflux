#!/usr/bin/env python3
"""
Test script for DREES professional demographics integration
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_hub.drees import DREESClient, get_specialist_availability

async def test_drees_integration():
    """Test DREES professional demographics processing"""
    print("👨‍⚕️ Testing DREES Professional Demographics Integration")
    print("=" * 60)
    
    client = DREESClient()
    
    # Process key professions for MVP
    print("📊 Processing DREES professional demographics...")
    results = await client.process_key_professions()
    
    print(f"✅ Processed:")
    for profession, count in results.items():
        print(f"   - {profession}: {count} records")
    
    # Test professional density queries
    print("\n🔍 Testing professional density queries...")
    
    # General practitioners density
    gp_densities = await client.get_professional_density_by_region(profession='medecins')
    print(f"Found density data for {len(gp_densities)} territories (Doctors)")
    
    if gp_densities[:5]:
        print("\nTop 5 territories by doctor density:")
        for i, density in enumerate(gp_densities[:5], 1):
            print(f"{i}. {density['territory_name']} ({density['territory_code']})")
            print(f"   - {density['professional_count']} doctors, {density['density_per_100k']:.1f}/100k")
            print(f"   - Density: {density['density_category']}")
    
    # Nurse density
    nurse_densities = await client.get_professional_density_by_region(profession='infirmieres_liberales')
    print(f"\nFound density data for {len(nurse_densities)} territories (Liberal nurses)")
    
    # Test low-density area identification
    print("\n⚠️ Testing shortage area identification...")
    
    low_density_gp = await client.get_low_density_areas(profession='medecins', max_density=80)
    print(f"Found {len(low_density_gp)} areas with doctor shortage (<80/100k)")
    
    if low_density_gp[:3]:
        print("\nTop 3 doctor shortage areas:")
        for i, area in enumerate(low_density_gp[:3], 1):
            print(f"{i}. {area['territory_name']} ({area['territory_code']})")
            print(f"   - {area['professional_count']} doctors, {area['density_per_100k']:.1f}/100k")
            print(f"   - Shortage severity: {area['shortage_severity']}")
    
    # Test specialist availability service
    print("\n💡 Testing specialist availability service...")
    
    # Test for Paris (75)
    paris_cardio = await get_specialist_availability("cardiology", "75000")
    if paris_cardio:
        print(f"Cardiology availability in Paris:")
        cardio = paris_cardio[0]
        print(f"- {cardio['professional_count']} specialists, {cardio['density_per_100k']:.1f}/100k")
        print(f"- {cardio['wait_estimate']}")
        print(f"- {cardio['recommendation']}")
    
    # Test for a rural area (e.g., Lozère - 48)
    rural_gp = await get_specialist_availability("general", "48000")
    if rural_gp:
        print(f"\nDoctor availability in rural area (48):")
        gp = rural_gp[0]
        print(f"- {gp['professional_count']} doctors, {gp['density_per_100k']:.1f}/100k")
        print(f"- {gp['wait_estimate']}")
        print(f"- {gp['recommendation']}")
    
    print("\n✅ DREES integration test completed successfully!")
    return results

if __name__ == "__main__":
    asyncio.run(test_drees_integration())
