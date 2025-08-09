#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from intelligence.condition_extractor import MedicalConditionExtractor

def test_condition_extractor():
    print("Testing Intelligent Condition Extractor...")
    print("=" * 50)
    
    # Initialize extractor
    extractor = MedicalConditionExtractor()
    
    test_queries = [
        "J'ai des problèmes d'hypertension",
        "Je souffre de mal de dos",
        "Infection urinaire récurrente", 
        "Mon diabète de type 2 n'est pas bien contrôlé",
        "Brûlures en urinant depuis 3 jours",
        "Ma tension est trop élevée"
    ]
    
    for query in test_queries:
        try:
            result = extractor.extract_condition(query)
            print(f"Query: {query}")
            if result:
                print(f"  ✓ Extracted: {result.condition}")
                print(f"  ✓ Confidence: {result.confidence:.2f}")
                print(f"  ✓ Category: {result.category}")
            else:
                print("  ✗ No condition extracted")
            print()
        except Exception as e:
            print(f"  ERROR: {e}")
            print()

if __name__ == "__main__":
    test_condition_extractor()
