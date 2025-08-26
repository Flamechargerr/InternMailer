#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE SYSTEM VALIDATION - InternMailing v2.1
======================================================
Tests all critical fixes including database prefix corruption fix
"""

import sys
import re
from pathlib import Path

# Add current directory to path
sys.path.append('.')

def test_database_prefix_fix():
    """🔧 Test the critical database prefix corruption fix"""
    print("🚀 TESTING DATABASE PREFIX CORRUPTION FIX")
    print("=" * 80)
    
    # Import the system
    try:
        from system import VerifiedEmailSystem
        system = VerifiedEmailSystem()
        print("✅ System imported successfully")
    except Exception as e:
        print(f"❌ Failed to import system: {e}")
        return False
    
    # Test cases based on your actual failures
    test_cases = [
        {
            'original': '0001.shivani@upenn.edu',
            'expected': 'shivani@upenn.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.shuchi@utexas.edu',
            'expected': 'shuchi@utexas.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.shweta@illinois.edu',
            'expected': 'shweta@illinois.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.siddharth@arizona.edu',
            'expected': 'siddharth@arizona.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.simon@washington.edu',
            'expected': 'simon@washington.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.song@ou.edu',
            'expected': 'song@ou.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.srijita@umich.edu',
            'expected': 'srijita@umich.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.sriram@colorado.edu',
            'expected': 'sriram@colorado.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '0001.stephen@wisc.edu',
            'expected': 'stephen@wisc.edu',
            'issue': 'Database prefix 0001.'
        },
        {
            'original': '12345.professor@mit.edu',
            'expected': 'professor@mit.edu',
            'issue': 'Database prefix 12345.'
        },
        {
            'original': 'id123.researcher@stanford.edu',
            'expected': 'researcher@stanford.edu',
            'issue': 'Database prefix id123.'
        },
        {
            'original': 'row456.faculty@harvard.edu',
            'expected': 'faculty@harvard.edu',
            'issue': 'Database prefix row456.'
        }
    ]
    
    print("🔧 DATABASE PREFIX CLEANING TESTS:")
    print("=" * 80)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\\n🧪 Test Case {i}: {case['issue']}")
        print(f"   Original: {case['original']}")
        print(f"   Expected: {case['expected']}")
        
        # Test the email cleaning
        cleaned_email = system.clean_email_address(case['original'])
        
        if cleaned_email == case['expected']:
            print(f"   ✅ SUCCESS: {case['original']} → {cleaned_email}")
            success_count += 1
        else:
            print(f"   ❌ FAILED: {case['original']} → {cleaned_email}")
            print(f"      Expected: {case['expected']}")
    
    print("\\n" + "=" * 80)
    print("📊 DATABASE PREFIX FIX RESULTS:")
    print("=" * 80)
    print(f"✅ Success Rate: {success_count}/{total_count} ({(success_count/total_count*100):.1f}%)")
    
    if success_count == total_count:
        print("🎉 ALL DATABASE PREFIX TESTS PASSED!")
        print("✅ Database corruption detection: WORKING")
        print("✅ Prefix removal: FUNCTIONAL")
        print("✅ Email validation: OPERATIONAL")
        return True
    else:
        print("⚠️  Some database prefix tests failed")
        return False

def test_content_variation_system():
    """🎨 Test content variation system"""
    print("\\n🚀 TESTING CONTENT VARIATION SYSTEM")
    print("=" * 80)
    
    try:
        from system import VerifiedEmailSystem
        system = VerifiedEmailSystem()
        
        # Test content variation
        variation_system = system._content_variation_system
        
        # Test research area variations
        base_area = "computer science"
        variations = []
        for i in range(5):
            varied = variation_system.get_varied_research_area(base_area, f"context{i}")
            variations.append(varied)
        
        unique_variations = len(set(variations))
        print(f"🎭 Research Area Variations: {unique_variations}/5 unique")
        for i, var in enumerate(variations, 1):
            print(f"   {i}. {var}")
        
        # Test repetition elimination
        repetitive_text = "computer science research in computer science with computer science methods"
        cleaned_text = variation_system.eliminate_repetition_in_text(repetitive_text, "TestProf")
        
        before_count = repetitive_text.lower().count('computer science')
        after_count = cleaned_text.lower().count('computer science')
        
        print(f"\\n📝 Repetition Elimination:")
        print(f"   Before: 'computer science' appears {before_count} times")
        print(f"   After: 'computer science' appears {after_count} times")
        print(f"   Reduction: {((before_count - after_count) / before_count * 100):.1f}%")
        
        return unique_variations >= 3 and after_count < before_count
        
    except Exception as e:
        print(f"❌ Content variation test failed: {e}")
        return False

def test_university_contamination_fix():
    """🌍 Test university contamination detection and fixing"""
    print("\\n🚀 TESTING UNIVERSITY CONTAMINATION FIX")
    print("=" * 80)
    
    try:
        from system import VerifiedEmailSystem
        system = VerifiedEmailSystem()
        
        contamination_cases = [
            {
                'original': 'leuvenbelgiumdaan.huybrechs@kuleuven.be',
                'expected': 'daan.huybrechs@kuleuven.be',
                'issue': 'Belgium university contamination'
            },
            {
                'original': 'pregradocruz@uc.cl',
                'expected': 'cruz@uc.cl', 
                'issue': 'Spanish pregrado contamination'
            },
            {
                'original': 'stanfordusajohn.smith@stanford.edu',
                'expected': 'john.smith@stanford.edu',
                'issue': 'USA university contamination'
            },
            {
                'original': 'universidadgarcia@unam.mx',
                'expected': 'garcia@unam.mx',
                'issue': 'Spanish universidad contamination'
            }
        ]
        
        success_count = 0
        for i, case in enumerate(contamination_cases, 1):
            print(f"\\n🧪 Test {i}: {case['issue']}")
            print(f"   Original: {case['original']}")
            
            cleaned = system.clean_email_address(case['original'])
            if cleaned == case['expected']:
                print(f"   ✅ SUCCESS: → {cleaned}")
                success_count += 1
            else:
                print(f"   ❌ FAILED: → {cleaned}")
                print(f"      Expected: {case['expected']}")
        
        print(f"\\n📊 University contamination fix: {success_count}/{len(contamination_cases)} passed")
        return success_count == len(contamination_cases)
        
    except Exception as e:
        print(f"❌ University contamination test failed: {e}")
        return False

def test_configuration_validation():
    """🔧 Test configuration system"""
    print("\\n🚀 TESTING CONFIGURATION SYSTEM")
    print("=" * 80)
    
    try:
        from config import config
        
        # Test configuration loading
        summary = config.get_config_summary()
        issues = config.validate_config()
        
        print("📊 Configuration Summary:")
        for key, value in summary.items():
            print(f"   ✅ {key}: {value}")
        
        if issues:
            print("\\n⚠️ Configuration Issues:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\\n🎉 Configuration is valid!")
        
        # Test database paths
        db_paths = config.get_database_paths()
        print("\\n📊 Database Paths:")
        for name, path in db_paths.items():
            print(f"   📁 {name}: {path}")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_system_integration():
    """🔄 Test overall system integration"""
    print("\\n🚀 TESTING SYSTEM INTEGRATION")
    print("=" * 80)
    
    try:
        from system import VerifiedEmailSystem
        
        # Test system initialization
        print("🔧 Initializing system...")
        system = VerifiedEmailSystem()
        print("✅ System initialized successfully")
        
        # Test content variation system integration
        if hasattr(system, '_content_variation_system'):
            print("✅ Content variation system integrated")
        else:
            print("❌ Content variation system missing")
            return False
        
        # Test email cleaning integration
        test_email = "0001.test@example.edu"
        cleaned = system.clean_email_address(test_email)
        if cleaned == "test@example.edu":
            print("✅ Database prefix fix integrated")
        else:
            print(f"❌ Database prefix fix failed: {test_email} → {cleaned}")
            return False
        
        print("✅ All system components integrated successfully")
        return True
        
    except Exception as e:
        print(f"❌ System integration test failed: {e}")
        return False

def main():
    """🎯 Main test runner"""
    print("🚀 INTERNMAILING v2.1 - COMPREHENSIVE SYSTEM VALIDATION")
    print("=" * 80)
    print("Testing all critical fixes and improvements...")
    print()
    
    tests = [
        ("Database Prefix Fix", test_database_prefix_fix),
        ("Content Variation System", test_content_variation_system),
        ("University Contamination Fix", test_university_contamination_fix),
        ("Configuration System", test_configuration_validation),
        ("System Integration", test_system_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Final results
    print("\\n" + "🎉" * 30)
    print("🏆 FINAL VALIDATION RESULTS")
    print("🎉" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} - {test_name}")
    
    print(f"\\n📊 Overall Success Rate: {passed}/{total} ({(passed/total*100):.1f}%)")
    
    if passed == total:
        print("\\n🎉 ALL TESTS PASSED - SYSTEM READY FOR GITHUB!")
        print("✅ Database prefix corruption: FIXED")
        print("✅ Content variation: WORKING")
        print("✅ University contamination: RESOLVED")
        print("✅ Configuration management: OPERATIONAL")
        print("✅ System integration: SUCCESSFUL")
        print("\\n🚀 Ready to push to GitHub as InternMailing v2.1!")
    else:
        print("\\n⚠️  Some tests failed - please review and fix issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)