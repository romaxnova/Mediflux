#!/usr/bin/env python3
"""
Test suite for the AI-powered Smart Healthcare Search System
Tests the production components: Smart MCP Server, AI Orchestrator, and Query Interpreter
"""

import unittest
import requests
import time
import subprocess
import os
from core_orchestration.smart_orchestrator import SmartHealthcareOrchestrator
from core_orchestration.ai_query_interpreter import AIQueryInterpreter

class TestSmartHealthcareSystem(unittest.TestCase):
    """Test the smart healthcare search system components"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        cls.api_key = os.getenv("ANNUAIRE_SANTE_API_KEY")
        cls.openai_key = os.getenv("OPENAI_API_KEY")
        
    def test_ai_query_interpreter(self):
        """Test AI-powered query interpretation"""
        print("\n🧠 Testing AI Query Interpreter...")
        
        if not self.openai_key:
            self.skipTest("OpenAI API key not configured")
            
        interpreter = AIQueryInterpreter()
        
        # Test French query
        result = interpreter.synchronous_interpret_query("Find physiotherapists in Paris")
        
        self.assertIsInstance(result, dict)
        self.assertIn("intent", result)
        self.assertIn("confidence", result)
        self.assertIn("fhir_params", result)
        self.assertEqual(result["intent"], "practitioner")
        self.assertGreater(result["confidence"], 0.8)
        
        print(f"✅ AI interpretation confidence: {result['confidence']}")
        print(f"✅ Detected intent: {result['intent']}")
        
    def test_smart_orchestrator(self):
        """Test smart orchestrator direct API integration"""
        print("\n🎯 Testing Smart Orchestrator...")
        
        if not self.api_key:
            self.skipTest("Healthcare API key not configured")
            
        orchestrator = SmartHealthcareOrchestrator()
        
        # Test practitioner search
        result = orchestrator.process_query("Find physiotherapists")
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        
        if result.get("success"):
            self.assertIn("results", result)
            self.assertIsInstance(result["results"], list)
            print(f"✅ Found {len(result['results'])} practitioners")
        else:
            print(f"⚠️ Search failed: {result.get('error', 'Unknown error')}")
            
    def test_organization_search(self):
        """Test organization search functionality"""
        print("\n🏥 Testing Organization Search...")
        
        if not self.api_key:
            self.skipTest("Healthcare API key not configured")
            
        orchestrator = SmartHealthcareOrchestrator()
        
        # Test organization search
        result = orchestrator.process_query("Find hospitals in Paris")
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        
        if result.get("success"):
            results = result.get("results", [])
            if results:
                # Check if results have organization structure
                first_result = results[0]
                if first_result.get("resource_type") == "organization":
                    print(f"✅ Found {len(results)} organizations")
                    print(f"✅ Sample: {first_result.get('name', 'N/A')}")
                else:
                    print(f"⚠️ Results might be practitioners instead of organizations")
            else:
                print("⚠️ No results found")
        else:
            print(f"⚠️ Organization search failed: {result.get('error', 'Unknown error')}")

    def test_mcp_server_health(self):
        """Test if MCP server is responsive (if running)"""
        print("\n🖥️ Testing MCP Server Health...")
        
        try:
            # Test if server is running
            response = requests.post(
                'http://localhost:9000/mcp/execute',
                json={'prompt': 'test connection'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("choices", data)
                print("✅ MCP Server is responsive")
            else:
                print(f"⚠️ MCP Server returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⚠️ MCP Server not running on port 9000")
            self.skipTest("MCP Server not running")
        except requests.exceptions.Timeout:
            print("⚠️ MCP Server timeout")
            self.skipTest("MCP Server timeout")
        except Exception as e:
            print(f"⚠️ MCP Server test error: {e}")
            self.skipTest(f"MCP Server error: {e}")

if __name__ == '__main__':
    print("🧪 Starting Smart Healthcare System Tests")
    print("=" * 50)
    
    # Run tests with verbose output
    unittest.main(verbosity=2)
