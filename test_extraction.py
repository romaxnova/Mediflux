#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/romanstadnikov/Desktop/Mediflux')
sys.path.append('/Users/romanstadnikov/Desktop/Mediflux/modules')

from modules.intelligence.condition_extractor import MedicalConditionExtractor

def test_extraction():
    extractor = MedicalConditionExtractor()
    
    test_cases = [
        "Je me sens fatigué depuis 3 semaines",
        "J'ai mal à la tête",
        "J'ai des problèmes d'hypertension",
        "infection urinaire"
    ]
    
    for query in test_cases:
        result = extractor.extract_condition(query)
        print(f"Query: '{query}'")
        print(f"Result: {result}")
        print("---")

if __name__ == "__main__":
    test_extraction()
