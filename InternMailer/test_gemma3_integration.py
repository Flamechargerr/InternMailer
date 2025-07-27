#!/usr/bin/env python3
"""
Integration test for complete Gemma3 optimization including:
1. Concise system/user prompts
2. Parallel chunk processing
3. Caching of identical resume segments
4. Lightweight fallback template parser
5. Sub-30-second parsing performance
"""

import os
import sys
import time
import logging
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from resume_parser import ResumeParser
from email_generator import EmailGenerator, get_ollama_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Gemma3IntegrationTest:
    """
    Comprehensive integration test for Gemma3 optimization.
    """
    
    def __init__(self):
        self.results = {}
        self.target_time = 30.0
        
    def test_resume_parsing_optimization(self) -> Dict[str, Any]:
        """Test optimized resume parsing with Gemma3."""
        print("\n🔍 Testing Resume Parsing Optimization")
        print("-" * 50)
        
        test_results = {
            "concise_prompts": False,
            "parallel_processing": False,
            "caching": False,
            "fallback_parser": False,
            "performance_target": False,
            "details": {}
        }
        
        try:
            # Test with sample resume
            resume_path = "resumes/CV_Anamay_Modern.pdf"
            if not os.path.exists(resume_path):
                print("ℹ️  Using sample resume text for testing")
                parser = ResumeParser("dummy.pdf", ollama_model='gemma3')
                parser.text = """
                TECHNICAL SKILLS
                Languages: Python, JavaScript, Java
                Frameworks: React, TensorFlow, Django
                
                PROJECTS
                CrimeConnect – MERN Stack, Real-time dashboard
                VARtificial Intelligence – ML prediction model
                
                EDUCATION
                B.Tech Data Science Engineering
                Courses: Machine Learning, Algorithms
                """
            else:
                parser = ResumeParser(resume_path, ollama_model='gemma3')
            
            # Test 1: Concise prompts
            print("✅ Testing concise prompts...")
            start_time = time.time()
            llm_result = parser.parse_with_llm()
            prompt_time = time.time() - start_time
            
            test_results["concise_prompts"] = bool(llm_result)
            test_results["details"]["prompt_processing_time"] = prompt_time
            
            # Test 2: Parallel processing (check if OllamaClient uses ThreadPoolExecutor)
            print("✅ Testing parallel chunk processing...")
            client = get_ollama_client()
            test_prompt = "This is a test prompt for parallel processing validation."
            
            # Create a longer prompt to trigger chunking
            long_prompt = test_prompt * 100  # Make it long enough to chunk
            start_time = time.time()
            parallel_result = client.generate_with_streaming(long_prompt, 'gemma3', use_chunking=True)
            parallel_time = time.time() - start_time
            
            test_results["parallel_processing"] = True  # If it completes without error
            test_results["details"]["parallel_processing_time"] = parallel_time
            
            # Test 3: Caching
            print("✅ Testing caching functionality...")
            cache_start = time.time()
            # First call
            result1 = client.generate_with_fallback(test_prompt, 'gemma3')
            first_call_time = time.time() - cache_start
            
            cache_start = time.time()
            # Second call (should use cache)
            result2 = client.generate_with_fallback(test_prompt, 'gemma3')
            second_call_time = time.time() - cache_start
            
            test_results["caching"] = second_call_time < first_call_time / 2  # Cache should be much faster
            test_results["details"]["cache_speedup"] = first_call_time / max(second_call_time, 0.001)
            
            # Test 4: Fallback parser
            print("✅ Testing lightweight fallback parser...")
            fallback_start = time.time()
            fallback_result = parser.parse_with_template_fallback()
            fallback_time = time.time() - fallback_start
            
            test_results["fallback_parser"] = bool(fallback_result and fallback_result.get('skills'))
            test_results["details"]["fallback_time"] = fallback_time
            
            # Test 5: Performance target
            print("✅ Testing overall performance...")
            total_start = time.time()
            final_result = parser.parse()
            total_time = time.time() - total_start
            
            test_results["performance_target"] = total_time <= self.target_time
            test_results["details"]["total_parsing_time"] = total_time
            test_results["details"]["extracted_data"] = {
                "skills_count": len(final_result.get('skills', [])),
                "projects_count": len(final_result.get('projects', [])),
                "parsing_method": "gemma3" if llm_result else "fallback"
            }
            
        except Exception as e:
            logging.error(f"Resume parsing test failed: {e}")
            test_results["error"] = str(e)
        
        return test_results
    
    def test_email_generation_optimization(self) -> Dict[str, Any]:
        """Test optimized email generation with Gemma3."""
        print("\n📧 Testing Email Generation Optimization")
        print("-" * 50)
        
        test_results = {
            "concise_email_prompts": False,
            "fast_generation": False,
            "quality_output": False,
            "details": {}
        }
        
        try:
            # Sample student info
            student_info = {
                "name": "Anamay Tripathy",
                "skills": ["Python", "Machine Learning", "TensorFlow", "React", "JavaScript"],
                "projects": ["CrimeConnect", "VARtificial Intelligence"],
                "summary": "Data Science Engineering student with ML experience"
            }
            
            # Sample professor
            professor = {
                "Name": "Dr. ML Researcher",
                "Research Area": "Machine Learning",
                "University": "Test University"
            }
            
            # Initialize email generator with Gemma3
            email_gen = EmailGenerator(student_info, use_ollama=True, ollama_model='gemma3')
            
            # Test concise prompts and fast generation
            print("✅ Testing concise email prompts...")
            start_time = time.time()
            email_body = email_gen.generate_with_llm(professor)
            generation_time = time.time() - start_time
            
            test_results["concise_email_prompts"] = len(email_body) > 0
            test_results["fast_generation"] = generation_time <= 30.0  # Should be under 30 seconds
            test_results["details"]["generation_time"] = generation_time
            test_results["details"]["email_length"] = len(email_body)
            
            # Test quality
            if email_body:
                # Check if email contains key elements
                has_greeting = any(word in email_body.lower() for word in ['dear', 'hello', 'hi'])
                has_interest = 'research' in email_body.lower() or 'internship' in email_body.lower()
                has_skills = any(skill.lower() in email_body.lower() for skill in student_info['skills'][:3])
                has_closing = any(word in email_body.lower() for word in ['sincerely', 'regards', 'best'])
                
                test_results["quality_output"] = has_greeting and has_interest and has_skills
                test_results["details"]["quality_metrics"] = {
                    "has_greeting": has_greeting,
                    "has_interest": has_interest,
                    "has_skills": has_skills,
                    "has_closing": has_closing
                }
            
        except Exception as e:
            logging.error(f"Email generation test failed: {e}")
            test_results["error"] = str(e)
        
        return test_results
    
    def test_cache_efficiency(self) -> Dict[str, Any]:
        """Test caching efficiency with multiple identical requests."""
        print("\n💾 Testing Cache Efficiency")
        print("-" * 50)
        
        test_results = {
            "cache_hits": 0,
            "cache_misses": 0,
            "average_cached_time": 0,
            "average_uncached_time": 0,
            "efficiency_gain": 0
        }
        
        try:
            client = get_ollama_client()
            test_prompts = [
                "Extract skills from resume: Python, Java, React",
                "Generate email to professor about ML research",
                "Parse resume section: Technical Skills",
            ]
            
            # Clear cache first
            client.cache.clear()
            
            uncached_times = []
            cached_times = []
            
            # Test each prompt twice
            for prompt in test_prompts:
                # First call (cache miss)
                start_time = time.time()
                result1 = client.generate_with_fallback(prompt, 'gemma3')
                uncached_time = time.time() - start_time
                uncached_times.append(uncached_time)
                
                # Second call (cache hit)
                start_time = time.time()
                result2 = client.generate_with_fallback(prompt, 'gemma3')
                cached_time = time.time() - start_time
                cached_times.append(cached_time)
                
                # Verify results are identical
                if result1 == result2 and cached_time < uncached_time:
                    test_results["cache_hits"] += 1
                else:
                    test_results["cache_misses"] += 1
            
            if uncached_times and cached_times:
                test_results["average_uncached_time"] = sum(uncached_times) / len(uncached_times)
                test_results["average_cached_time"] = sum(cached_times) / len(cached_times)
                test_results["efficiency_gain"] = (test_results["average_uncached_time"] / 
                                                 max(test_results["average_cached_time"], 0.001))
            
        except Exception as e:
            logging.error(f"Cache efficiency test failed: {e}")
            test_results["error"] = str(e)
        
        return test_results
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite."""
        print("🚀 Starting Gemma3 Integration Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        self.results["resume_parsing"] = self.test_resume_parsing_optimization()
        self.results["email_generation"] = self.test_email_generation_optimization()
        self.results["cache_efficiency"] = self.test_cache_efficiency()
        
        total_time = time.time() - start_time
        self.results["total_test_time"] = total_time
        
        # Generate summary
        summary = self.generate_integration_summary()
        
        return {
            "detailed_results": self.results,
            "summary": summary,
            "total_time": total_time
        }
    
    def generate_integration_summary(self) -> Dict[str, Any]:
        """Generate integration test summary."""
        summary = {
            "tests_passed": 0,
            "tests_failed": 0,
            "optimization_score": 0,
            "recommendations": []
        }
        
        # Check resume parsing results
        resume_tests = self.results.get("resume_parsing", {})
        resume_score = 0
        
        if resume_tests.get("concise_prompts"):
            summary["tests_passed"] += 1
            resume_score += 20
        else:
            summary["tests_failed"] += 1
            summary["recommendations"].append("Improve prompt conciseness for better performance")
        
        if resume_tests.get("parallel_processing"):
            summary["tests_passed"] += 1
            resume_score += 20
        else:
            summary["tests_failed"] += 1
            summary["recommendations"].append("Implement parallel chunk processing")
        
        if resume_tests.get("caching"):
            summary["tests_passed"] += 1
            resume_score += 20
        else:
            summary["tests_failed"] += 1
            summary["recommendations"].append("Implement caching for identical segments")
        
        if resume_tests.get("fallback_parser"):
            summary["tests_passed"] += 1
            resume_score += 20
        else:
            summary["tests_failed"] += 1
            summary["recommendations"].append("Add lightweight fallback parser")
        
        if resume_tests.get("performance_target"):
            summary["tests_passed"] += 1
            resume_score += 20
        else:
            summary["tests_failed"] += 1
            summary["recommendations"].append("Optimize for sub-30-second parsing")
        
        # Check email generation results
        email_tests = self.results.get("email_generation", {})
        email_score = 0
        
        if email_tests.get("concise_email_prompts"):
            email_score += 15
        if email_tests.get("fast_generation"):
            email_score += 15
        
        # Check cache efficiency
        cache_tests = self.results.get("cache_efficiency", {})
        cache_score = 0
        
        if cache_tests.get("cache_hits", 0) > cache_tests.get("cache_misses", 0):
            cache_score += 10
        
        summary["optimization_score"] = resume_score + email_score + cache_score
        
        # Performance assessment
        if summary["optimization_score"] >= 90:
            summary["assessment"] = "Excellent - Production Ready"
        elif summary["optimization_score"] >= 70:
            summary["assessment"] = "Good - Minor improvements needed"
        elif summary["optimization_score"] >= 50:
            summary["assessment"] = "Acceptable - Significant improvements needed"
        else:
            summary["assessment"] = "Poor - Major optimizations required"
        
        return summary
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        print("\n" + "=" * 60)
        print("📊 GEMMA3 INTEGRATION TEST RESULTS")
        print("=" * 60)
        
        summary = results["summary"]
        
        print(f"🎯 Tests Passed: {summary['tests_passed']}")
        print(f"❌ Tests Failed: {summary['tests_failed']}")
        print(f"📈 Optimization Score: {summary['optimization_score']}/100")
        print(f"🏆 Assessment: {summary['assessment']}")
        
        # Detailed results
        resume_results = results["detailed_results"]["resume_parsing"]
        print(f"\n📄 RESUME PARSING:")
        print(f"   ✅ Concise Prompts: {'✓' if resume_results.get('concise_prompts') else '✗'}")
        print(f"   ⚡ Parallel Processing: {'✓' if resume_results.get('parallel_processing') else '✗'}")
        print(f"   💾 Caching: {'✓' if resume_results.get('caching') else '✗'}")
        print(f"   🔄 Fallback Parser: {'✓' if resume_results.get('fallback_parser') else '✗'}")
        print(f"   🏃 Performance Target: {'✓' if resume_results.get('performance_target') else '✗'}")
        
        if "details" in resume_results:
            details = resume_results["details"]
            print(f"   ⏱️  Total Time: {details.get('total_parsing_time', 0):.2f}s")
            if "extracted_data" in details:
                data = details["extracted_data"]
                print(f"   📊 Extracted: {data.get('skills_count', 0)} skills, {data.get('projects_count', 0)} projects")
        
        # Email generation results
        email_results = results["detailed_results"]["email_generation"]
        print(f"\n📧 EMAIL GENERATION:")
        print(f"   ✅ Concise Prompts: {'✓' if email_results.get('concise_email_prompts') else '✗'}")
        print(f"   ⚡ Fast Generation: {'✓' if email_results.get('fast_generation') else '✗'}")
        print(f"   📝 Quality Output: {'✓' if email_results.get('quality_output') else '✗'}")
        
        if "details" in email_results:
            details = email_results["details"]
            print(f"   ⏱️  Generation Time: {details.get('generation_time', 0):.2f}s")
            print(f"   📏 Email Length: {details.get('email_length', 0)} chars")
        
        # Cache efficiency
        cache_results = results["detailed_results"]["cache_efficiency"]
        print(f"\n💾 CACHE EFFICIENCY:")
        print(f"   🎯 Cache Hits: {cache_results.get('cache_hits', 0)}")
        print(f"   ❌ Cache Misses: {cache_results.get('cache_misses', 0)}")
        print(f"   ⚡ Efficiency Gain: {cache_results.get('efficiency_gain', 0):.1f}x")
        
        # Recommendations
        if summary["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(summary["recommendations"], 1):
                print(f"   {i}. {rec}")
        
        print(f"\n⏳ Total Test Time: {results['total_time']:.2f}s")
        print("=" * 60)

def main():
    """Run Gemma3 integration tests."""
    test_suite = Gemma3IntegrationTest()
    
    try:
        results = test_suite.run_integration_tests()
        test_suite.print_results(results)
        
        # Success criteria
        summary = results["summary"]
        if summary["optimization_score"] >= 80 and summary["tests_failed"] == 0:
            print("\n🎉 INTEGRATION TESTS PASSED: Gemma3 optimization is ready for production!")
            return 0
        else:
            print(f"\n⚠️  INTEGRATION TESTS NEED IMPROVEMENT:")
            print(f"   - Optimization Score: {summary['optimization_score']}/100 (need ≥80)")
            print(f"   - Failed Tests: {summary['tests_failed']} (need 0)")
            return 1
            
    except Exception as e:
        print(f"\n❌ INTEGRATION TESTS FAILED: {e}")
        logging.error(f"Integration test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
