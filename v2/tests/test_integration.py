"""
Integration Tests
Tests for component integration and workflows
"""

import asyncio
import os
import sys

# Add modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(os.path.dirname(current_dir), 'modules')
sys.path.insert(0, modules_dir)

async def test_orchestrator_workflow():
    """Test main orchestrator integration"""
    try:
        from orchestrator import MedifluxOrchestrator
        
        orchestrator = MedifluxOrchestrator()
        
        # Test query processing
        result = await orchestrator.process_query("Test query", "test_integration_user")
        
        # Should have basic structure
        has_intent = "intent" in result
        has_success = "success" in result
        
        return has_intent and has_success
        
    except Exception:
        return False
