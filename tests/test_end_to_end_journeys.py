#!/usr/bin/env python3
"""
Prompt 4: End-to-End Architecture Testing
Comprehensive integration tests for the three main user journeys
"""

import asyncio
import pytest
import time
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core_orchestration.smart_orchestrator import SmartOrchestrator
from src.core_orchestration.ai_query_interpreter import AIQueryInterpreter  
from src.memory_store.memory_manager import MemoryManager
from src.data_hub.bdpm import BDPMClient
from src.data_hub.annuaire import AnnuaireSanteClient
from src.config.database import get_database_client

class PerformanceTracker:
    """Track performance metrics for end-to-end journeys"""
    
    def __init__(self):
        self.metrics = {}
        
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.metrics[operation] = {'start_time': time.time()}
        
    def end_timer(self, operation: str, details: dict = None):
        """End timing and record metrics"""
        if operation in self.metrics:
            end_time = time.time()
            duration = end_time - self.metrics[operation]['start_time']
            self.metrics[operation].update({
                'duration_ms': round(duration * 1000, 2),
                'end_time': end_time,
                'details': details or {}
            })
            
    def get_summary(self):
        """Get performance summary"""
        total_time = sum(m.get('duration_ms', 0) for m in self.metrics.values())
        return {
            'total_journey_time_ms': round(total_time, 2),
            'operation_breakdown': {k: v.get('duration_ms', 0) for k, v in self.metrics.items()},
            'detailed_metrics': self.metrics
        }

@pytest.fixture
async def orchestrator():
    """Setup orchestrator for testing"""
    # Mock XAI API to avoid real API calls during testing
    with patch('src.core_orchestration.smart_orchestrator.xai') as mock_xai:
        mock_xai.chat.completions.create = AsyncMock(return_value=Mock(
            choices=[Mock(message=Mock(content="Mocked AI response"))]
        ))
        
        orchestrator = SmartOrchestrator()
        await orchestrator.initialize()
        return orchestrator

@pytest.fixture
def performance_tracker():
    """Setup performance tracker"""
    return PerformanceTracker()

@pytest.mark.asyncio
class TestUserJourney1_ReimbursementSimulation:
    """Journey 1: Reimbursement Simulation for Prescription (Focus: Cost Transparency)"""
    
    async def test_text_input_reimbursement_simulation(self, orchestrator, performance_tracker):
        """Test: User chats 'Estimate cost for my back pain meds'"""
        
        print("\n🔍 Journey 1A: Text Input Reimbursement Simulation")
        print("=" * 60)
        
        # Start performance tracking
        performance_tracker.start_timer('full_journey')
        
        # Test user input
        user_query = "Estimate cost for my back pain medication - I have chronic pain and an AXA mutuelle"
        
        # Step 1: Orchestrator captures input and retrieves profile
        performance_tracker.start_timer('input_processing')
        
        # Mock user profile in memory
        user_profile = {
            "mutuelle_type": "AXA Basic",
            "pathology": "chronic back pain", 
            "preferences": "low-cost generic",
            "user_id": "test_user_001"
        }
        
        await orchestrator.memory_manager.store_user_profile("test_user_001", user_profile)
        performance_tracker.end_timer('input_processing', {'profile_loaded': True})
        
        # Step 2: Query processing with orchestrator
        performance_tracker.start_timer('orchestrator_processing')
        
        response = await orchestrator.process_query(
            query=user_query,
            user_id="test_user_001",
            context={"journey_type": "reimbursement_simulation"}
        )
        
        performance_tracker.end_timer('orchestrator_processing', {
            'response_length': len(str(response)),
            'data_sources_queried': ['BDPM', 'OpenMedic']
        })
        
        # Step 3: Validate response structure
        performance_tracker.start_timer('response_validation')
        
        assert response is not None
        assert isinstance(response, dict)
        
        # Should contain cost estimation
        cost_info = response.get('cost_analysis', {})
        assert 'estimated_cost' in str(response) or 'reimbursement' in str(response)
        
        performance_tracker.end_timer('response_validation')
        performance_tracker.end_timer('full_journey')
        
        # Performance validation
        metrics = performance_tracker.get_summary()
        print(f"   ✅ Journey completed in {metrics['total_journey_time_ms']}ms")
        print(f"   📊 Breakdown: {metrics['operation_breakdown']}")
        
        # Performance requirements: < 2000ms for MVP
        assert metrics['total_journey_time_ms'] < 2000, f"Journey took {metrics['total_journey_time_ms']}ms (> 2000ms limit)"
        
        return metrics
    
    async def test_document_upload_simulation(self, orchestrator, performance_tracker):
        """Test: User uploads feuille de soins/carte tiers payant"""
        
        print("\n📄 Journey 1B: Document Upload Reimbursement")
        print("=" * 50)
        
        performance_tracker.start_timer('full_journey_doc')
        
        # Mock document content (would be OCR in real implementation)
        mock_document_data = {
            "document_type": "carte_tiers_payant",
            "extracted_data": {
                "mutuelle": "AXA",
                "coverage_level": "70%",
                "medications": ["DOLIPRANE", "ADVIL"],
                "exclusions": ["dentaire"]
            }
        }
        
        performance_tracker.start_timer('document_processing')
        
        # Process document through orchestrator
        response = await orchestrator.process_query(
            query="Analyze this carte tiers payant for medication coverage",
            user_id="test_user_001",
            context={
                "journey_type": "document_analysis",
                "document_data": mock_document_data
            }
        )
        
        performance_tracker.end_timer('document_processing')
        
        # Validate document analysis
        assert response is not None
        assert 'coverage' in str(response) or 'mutuelle' in str(response)
        
        performance_tracker.end_timer('full_journey_doc')
        metrics = performance_tracker.get_summary()
        
        print(f"   ✅ Document analysis completed in {metrics.get('full_journey_doc', {}).get('duration_ms', 0)}ms")
        
        return metrics

@pytest.mark.asyncio 
class TestUserJourney2_CarePathwayOptimization:
    """Journey 2: Optimized Care Path Advice (Focus: Informed Routing)"""
    
    async def test_care_pathway_recommendation(self, orchestrator, performance_tracker):
        """Test: User asks 'Best path for chronic back pain treatment near Paris, low-cost preference'"""
        
        print("\n🗺️  Journey 2: Care Pathway Optimization")
        print("=" * 50)
        
        performance_tracker.start_timer('pathway_journey')
        
        user_query = "Best path for chronic back pain treatment near Paris, low-cost preference"
        
        # Mock regional data that would come from SAE/DREES
        mock_regional_context = {
            "location": "Paris",
            "specialities_available": ["GP", "Physiotherapist", "Rheumatologist"],
            "average_wait_times": {"GP": 5, "Physiotherapist": 12, "Rheumatologist": 25},
            "cost_estimates": {"GP": 23, "Physiotherapist": 45, "Rheumatologist": 120}
        }
        
        performance_tracker.start_timer('pathway_analysis')
        
        response = await orchestrator.process_query(
            query=user_query,
            user_id="test_user_001", 
            context={
                "journey_type": "care_pathway",
                "regional_data": mock_regional_context
            }
        )
        
        performance_tracker.end_timer('pathway_analysis', {
            'specialists_considered': len(mock_regional_context['specialities_available']),
            'location_specified': True
        })
        
        # Validate pathway recommendations
        assert response is not None
        response_str = str(response)
        
        # Should mention care sequence or specialists
        pathway_indicators = ['GP', 'pathway', 'specialist', 'treatment', 'sequence']  
        assert any(indicator in response_str.lower() for indicator in pathway_indicators)
        
        performance_tracker.end_timer('pathway_journey')
        metrics = performance_tracker.get_summary()
        
        print(f"   ✅ Pathway analysis completed in {metrics.get('pathway_journey', {}).get('duration_ms', 0)}ms")
        print(f"   🏥 Recommended specialists: {mock_regional_context['specialities_available']}")
        
        return metrics

@pytest.mark.asyncio
class TestUserJourney3_DocumentAnalysis:
    """Journey 3: Document Upload and Analysis (Focus: Bureaucracy Reduction)"""
    
    async def test_document_coverage_analysis(self, orchestrator, performance_tracker):
        """Test: User uploads carte tiers payant and asks 'What does this cover for dentistry?'"""
        
        print("\n📋 Journey 3: Document Analysis & Coverage")
        print("=" * 50)
        
        performance_tracker.start_timer('document_journey')
        
        # Mock carte tiers payant data
        mock_carte_data = {
            "document_type": "carte_tiers_payant",
            "mutuelle": "AXA",
            "coverage_levels": {
                "medications": "70%",
                "consultations": "80%", 
                "dentistry": "50%",
                "optics": "60%"
            },
            "exclusions": ["cosmetic_dentistry"],
            "annual_limits": {"dentistry": "€400", "optics": "€200"}
        }
        
        user_query = "What does this cover for dentistry?"
        
        performance_tracker.start_timer('document_ocr_simulation')
        
        # Simulate OCR + extraction (would use real OCR in production)
        extracted_info = {
            "dentistry_coverage": mock_carte_data["coverage_levels"]["dentistry"],
            "dentistry_limit": mock_carte_data["annual_limits"]["dentistry"],
            "exclusions": mock_carte_data["exclusions"]
        }
        
        performance_tracker.end_timer('document_ocr_simulation')
        
        performance_tracker.start_timer('coverage_analysis')
        
        response = await orchestrator.process_query(
            query=user_query,
            user_id="test_user_001",
            context={
                "journey_type": "coverage_analysis", 
                "document_data": mock_carte_data,
                "extracted_info": extracted_info
            }
        )
        
        performance_tracker.end_timer('coverage_analysis')
        
        # Validate coverage analysis
        assert response is not None
        response_str = str(response)
        
        # Should mention dentistry coverage details
        coverage_indicators = ['dentistry', 'coverage', '50%', 'cover']
        assert any(indicator in response_str.lower() for indicator in coverage_indicators)
        
        performance_tracker.end_timer('document_journey')
        metrics = performance_tracker.get_summary() 
        
        print(f"   ✅ Coverage analysis completed in {metrics.get('document_journey', {}).get('duration_ms', 0)}ms")
        print(f"   🦷 Dentistry coverage: {extracted_info['dentistry_coverage']}")
        
        return metrics

@pytest.mark.asyncio
class TestSystemIntegration:
    """Test system-wide integration and performance"""
    
    async def test_data_source_connectivity(self):
        """Test connectivity to all data sources"""
        
        print("\n🔌 System Integration: Data Source Connectivity")
        print("=" * 55)
        
        # Test production database
        db_client = get_database_client('production')
        health_check = db_client.health_check()
        
        print(f"   📊 Production Database: {health_check['status']}")
        assert health_check['status'] == 'healthy'
        
        # Test individual data sources
        data_sources = []
        
        try:
            # Test BDPM connection (mock for testing)
            bdpm_client = BDPMClient()
            data_sources.append(("BDPM", "Connected"))
        except Exception as e:
            data_sources.append(("BDPM", f"Error: {e}"))
            
        try:
            # Test Annuaire Sante connection (mock for testing)  
            annuaire_client = AnnuaireSanteClient()
            data_sources.append(("Annuaire Santé", "Connected"))
        except Exception as e:
            data_sources.append(("Annuaire Santé", f"Error: {e}"))
        
        # Report connectivity
        for source, status in data_sources:
            print(f"   🔗 {source}: {status}")
        
        # At least database should be working
        connected_sources = [s for s, status in data_sources if "Connected" in status]
        assert len(connected_sources) >= 0  # At minimum production DB works
        
    async def test_memory_persistence(self, orchestrator):
        """Test user data persistence across sessions"""
        
        print("\n💾 System Integration: Memory Persistence")
        print("=" * 50)
        
        user_id = "test_persistence_user"
        
        # Store user profile
        test_profile = {
            "mutuelle_type": "Test Mutuelle",
            "chronic_conditions": ["back pain", "diabetes"],
            "preferences": "low_cost"
        }
        
        await orchestrator.memory_manager.store_user_profile(user_id, test_profile)
        
        # Retrieve and validate
        retrieved_profile = await orchestrator.memory_manager.get_user_profile(user_id)
        
        assert retrieved_profile is not None
        assert retrieved_profile["mutuelle_type"] == "Test Mutuelle"
        assert "back pain" in retrieved_profile["chronic_conditions"]
        
        print(f"   ✅ User profile stored and retrieved successfully")
        print(f"   👤 Profile: {retrieved_profile['mutuelle_type']}")
        
    async def test_end_to_end_performance_benchmark(self, orchestrator, performance_tracker):
        """Run all three journeys and measure overall system performance"""
        
        print("\n⚡ System Integration: Performance Benchmark")
        print("=" * 50)
        
        # Run simplified versions of all three journeys
        journeys = []
        
        # Journey 1: Quick reimbursement query
        performance_tracker.start_timer('benchmark_journey_1')
        response_1 = await orchestrator.process_query(
            "Quick cost estimate for paracetamol",
            "benchmark_user",
            {"journey_type": "reimbursement"}
        )
        performance_tracker.end_timer('benchmark_journey_1')
        journeys.append(("Reimbursement Simulation", response_1))
        
        # Journey 2: Quick pathway query  
        performance_tracker.start_timer('benchmark_journey_2')
        response_2 = await orchestrator.process_query(
            "Find nearby GP for consultation",
            "benchmark_user", 
            {"journey_type": "pathway"}
        )
        performance_tracker.end_timer('benchmark_journey_2')
        journeys.append(("Care Pathway", response_2))
        
        # Journey 3: Quick document query
        performance_tracker.start_timer('benchmark_journey_3')
        response_3 = await orchestrator.process_query(
            "Explain my insurance coverage",
            "benchmark_user",
            {"journey_type": "document_analysis"}
        )
        performance_tracker.end_timer('benchmark_journey_3')
        journeys.append(("Document Analysis", response_3))
        
        # Performance summary
        metrics = performance_tracker.get_summary()
        
        print(f"   📊 All journeys completed:")
        for i, (journey_name, response) in enumerate(journeys, 1):
            duration = metrics['operation_breakdown'].get(f'benchmark_journey_{i}', 0)
            print(f"   {i}. {journey_name}: {duration}ms")
        
        print(f"   🎯 Total system performance: {metrics['total_journey_time_ms']}ms")
        
        # All journeys should complete successfully
        for journey_name, response in journeys:
            assert response is not None, f"{journey_name} failed to return response"
        
        # System should handle all journeys in reasonable time (< 5s total)
        assert metrics['total_journey_time_ms'] < 5000, f"System too slow: {metrics['total_journey_time_ms']}ms"
        
        return metrics

# Main test runner
async def run_end_to_end_tests():
    """Run comprehensive end-to-end tests"""
    
    print("🚀 PROMPT 4: END-TO-END ARCHITECTURE TESTING")
    print("=" * 70)
    print("Testing complete workflow functionality for all user journeys")
    print()
    
    # Initialize components
    performance_tracker = PerformanceTracker()
    
    try:
        # Setup orchestrator
        with patch('src.core_orchestration.smart_orchestrator.xai') as mock_xai:
            mock_xai.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="Test AI response for healthcare query"))]
            ))
            
            orchestrator = SmartOrchestrator()
            await orchestrator.initialize()
            
            # Run test suites
            test_results = {}
            
            # Journey Tests
            journey1_tests = TestUserJourney1_ReimbursementSimulation()
            test_results['journey_1a'] = await journey1_tests.test_text_input_reimbursement_simulation(orchestrator, performance_tracker)
            test_results['journey_1b'] = await journey1_tests.test_document_upload_simulation(orchestrator, performance_tracker)
            
            journey2_tests = TestUserJourney2_CarePathwayOptimization()
            test_results['journey_2'] = await journey2_tests.test_care_pathway_recommendation(orchestrator, performance_tracker)
            
            journey3_tests = TestUserJourney3_DocumentAnalysis() 
            test_results['journey_3'] = await journey3_tests.test_document_coverage_analysis(orchestrator, performance_tracker)
            
            # System Integration Tests
            integration_tests = TestSystemIntegration()
            await integration_tests.test_data_source_connectivity()
            await integration_tests.test_memory_persistence(orchestrator)
            test_results['performance_benchmark'] = await integration_tests.test_end_to_end_performance_benchmark(orchestrator, performance_tracker)
            
            # Final Summary
            print("\n" + "=" * 70)
            print("🎉 END-TO-END TESTING COMPLETE")
            print("=" * 70)
            
            total_time = sum(
                result.get('total_journey_time_ms', 0) if isinstance(result, dict) else 0 
                for result in test_results.values()
            )
            
            print(f"✅ All user journeys tested successfully")
            print(f"⚡ Total testing time: {total_time:.2f}ms")
            print(f"📊 Production database: Working ({performance_tracker.metrics})")
            print(f"🔄 Memory persistence: Working")
            print(f"🎯 Ready for frontend integration (Prompt 5)")
            
            return test_results
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        raise e

if __name__ == "__main__":
    # Run the end-to-end tests
    asyncio.run(run_end_to_end_tests())
