#!/usr/bin/env python3
"""
Debug Research Classification Issue
"""

from enhanced_research_area_inference import EnhancedResearchAreaInference

def debug_test():
    inference = EnhancedResearchAreaInference()
    
    test_case = {
        'name': 'Prof. Tyagi Brain Disease Classification via Causal Graph Structure Learning',
        'affiliation': 'Medical AI Research Institute'
    }
    
    print("🔍 DEBUGGING RESEARCH CLASSIFICATION")
    print("=" * 50)
    print(f"Input: {test_case}")
    
    # Check manual mappings
    name = test_case.get('name', '').lower()
    print(f"Looking for '{name}' in manual mappings...")
    
    # Check for partial matches
    for mapped_name, research_area in inference.manual_mappings.items():
        if any(part in name for part in mapped_name.split()):
            print(f"FOUND PARTIAL MATCH: '{mapped_name}' -> {research_area}")
    
    result = inference.infer_research_area(test_case)
    print(f"Final result: {result}")
    
    return result

if __name__ == "__main__":
    debug_test()
