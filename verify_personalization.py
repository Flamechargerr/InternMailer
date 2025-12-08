
from smart_research_system import get_smart_research_system

def test_personalization():
    system = get_smart_research_system()
    
    # Test Case 1: Generic "Computer Science" -> Should upgrade to specific title
    print("\n🧪 TEST 1: Generic 'Computer Science' with specific paper")
    papers = [{'title': 'Optimizing Deep Reinforcement Learning for Robotic Control'}]
    result = system._generate_personalized_content(
        name="Test Prof",
        primary_area="Computer Science",
        papers=papers,
        affiliation="MIT",
        confidence=0.5
    )
    print(f"   Input Area: Computer Science")
    print(f"   Paper Title: {papers[0]['title']}")
    print(f"   -> Result Area: {result['research_area']}")
    print(f"   -> Mention: {result['research_focus']}")
    
    if result['research_area'] == papers[0]['title']:
        print("   ✅ SUCCESS: Area upgraded to paper title")
    else:
        print(f"   ❌ FAILURE: Area remained {result['research_area']}")

    # Test Case 2: Already specific "Robotics" -> Should stay "Robotics"
    print("\n🧪 TEST 2: Specific 'Robotics' area")
    result = system._generate_personalized_content(
        name="Test Robotics",
        primary_area="Robotics",
        papers=papers,
        affiliation="MIT",
        confidence=0.8
    )
    print(f"   Input Area: Robotics")
    print(f"   -> Result Area: {result['research_area']}")
    
    if result['research_area'] == "Robotics":
        print("   ✅ SUCCESS: Specific area preserved")
    else:
        print(f"   ❌ FAILURE: Area changed to {result['research_area']}")

if __name__ == "__main__":
    test_personalization()
