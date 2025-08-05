"""
Core Component Tests
Tests for fundamental V2 components
"""

import asyncio
import sys
import os

# Add modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(os.path.dirname(current_dir), 'modules')
sys.path.insert(0, modules_dir)

async def test_imports():
    """Test all critical module imports"""
    modules_to_test = [
        ("interpreter.intent_router", "IntentRouter"),
        ("memory.store", "MemoryStore"),
        ("data_hub.bdpm", "BDPMClient"),
        ("data_hub.annuaire", "AnnuaireClient"),
        ("reimbursement.simulator", "ReimbursementSimulator"),
        ("orchestrator", "MedifluxOrchestrator")
    ]
    
    failed = []
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
        except Exception as e:
            failed.append(f"{module_name}.{class_name}: {e}")
    
    return len(failed) == 0

async def test_intent_routing():
    """Test intent routing functionality"""
    try:
        from interpreter.intent_router import IntentRouter
        router = IntentRouter()
        
        test_cases = [
            ("Combien coûte le Doliprane?", "simulate_cost"),
            ("Je cherche un cardiologue", "practitioner_search"),
        ]
        
        correct = 0
        for query, expected in test_cases:
            result = await router.route_intent(query)
            if result["intent"] == expected:
                correct += 1
        
        return correct >= len(test_cases) - 1  # Allow 1 failure
        
    except Exception:
        return False

async def test_memory_operations():
    """Test memory store operations"""
    try:
        from memory.store import MemoryStore
        memory = MemoryStore("test_core.db")
        
        # Test basic operations
        test_user = "test_core_user"
        await memory.update_user_profile(test_user, {"mutuelle": "test"})
        context = await memory.get_user_context(test_user)
        
        profile_ok = context["profile"].get("mutuelle") == "test"
        
        # Test session history
        await memory.update_session_history(test_user, "test", {"intent": "test"})
        updated = await memory.get_user_context(test_user)
        history_ok = len(updated["recent_history"]) > 0
        
        # Cleanup
        if os.path.exists("test_core.db"):
            os.remove("test_core.db")
        
        return profile_ok and history_ok
        
    except Exception:
        return False
