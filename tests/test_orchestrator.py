import unittest
import sys
from backend.core.orchestrator import HealthcareOrchestrator  # Updated import
from backend.core.intent_parser import IntentParser  # For confidence testing

import requests  # For real API calls

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = HealthcareOrchestrator()
    
    def test_extension_data_extraction(self):
        # Test with a sample query that should extract extensions
        query_result = self.orchestrator.process_query("find hospitals in 75013")
        self.assertIn("address", str(query_result), "Extension data (e.g., address) not found in response")
    
    def test_confidence_scoring(self):
        intent = IntentParser.parse("find doctors in Paris")
        self.assertGreaterEqual(intent.get("confidence", 0.0), 0.5, "Confidence score should be at least 0.5 for a matching query")
        low_confidence_intent = IntentParser.parse("find something unclear")
        self.assertLess(low_confidence_intent.get("confidence", 0.0), 0.5, "Confidence should be low for unclear queries")
    
    def test_fallback_strategy(self):
        result = self.orchestrator.process_query("ambiguous query")
        self.assertIn("Query unclear", str(result), "Fallback strategy not triggered")
    
    def test_real_api_response(self):
        # Simulate a real API call
        try:
            response = requests.get("http://localhost:8000/api/organization/search?name=clinique&postalCode=75013")
            response.raise_for_status()
            self.assertIn("extension", str(response.json()), "Extension data not in real API response")
        except requests.RequestException as e:
            self.fail(f"API call failed: {e}")
    
    def test_basic_functionality(self):
        query_result = self.orchestrator.process_query("find hospitals in Paris")
        self.assertIsNotNone(query_result, "Query processing returned a result")

if __name__ == "__main__":
    unittest.main()
