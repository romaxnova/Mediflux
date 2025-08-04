"""
V2 Test Suite Runner
Organized test management for Mediflux V2
"""

import asyncio
import os
import sys

# Add modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(os.path.dirname(current_dir), 'modules')
sys.path.insert(0, modules_dir)

async def run_core_tests():
    """Run core component tests"""
    print("🔧 Core Component Tests")
    print("-" * 30)
    
    # Import and run core functionality tests
    from test_core_components import test_imports, test_intent_routing, test_memory_operations
    
    results = []
    results.append(("Module Imports", await test_imports()))
    results.append(("Intent Routing", await test_intent_routing()))
    results.append(("Memory Operations", await test_memory_operations()))
    
    return results

async def run_database_tests():
    """Run database architecture tests"""
    print("\n💾 Database Architecture Tests")
    print("-" * 35)
    
    from test_database import test_database_manager, test_json_support
    
    results = []
    results.append(("Database Manager", await test_database_manager()))
    results.append(("JSON Support", await test_json_support()))
    
    return results

async def run_integration_tests():
    """Run integration tests"""
    print("\n🎼 Integration Tests")
    print("-" * 25)
    
    from test_integration import test_orchestrator_workflow
    
    results = []
    results.append(("Orchestrator Workflow", await test_orchestrator_workflow()))
    
    return results

async def main():
    """Run all test suites"""
    print("🚀 V2 MEDIFLUX TEST SUITE")
    print("=" * 35)
    
    all_results = []
    
    # Run test suites
    all_results.extend(await run_core_tests())
    all_results.extend(await run_database_tests())
    all_results.extend(await run_integration_tests())
    
    # Summary
    print("\n" + "=" * 35)
    print("📋 TEST SUITE SUMMARY")
    print("=" * 35)
    
    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    
    for test_name, result in all_results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
