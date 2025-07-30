"""
Llama Client for Email Generation
=================================
Provides Llama-based email generation as a fallback when Azure AI is unavailable.
Uses Llama API (Replicate, Together AI, or similar) for Llama model access.
"""

import os
import logging
import requests
import json
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlamaClient:
    """
    Llama client for email generation using Llama API services.
    Serves as a fallback when Azure AI is unavailable.
    """
    
    def __init__(self, api_key: str = None, model: str = None, provider: str = None):
        # Load configuration from environment
        self.provider = provider or os.getenv("LLAMA_PROVIDER", "replicate")  # replicate, together, huggingface, github
        self.api_key = api_key or os.getenv("LLAMA_API_KEY")
        self.model = model or os.getenv("LLAMA_MODEL", "meta/llama-2-70b-chat")
        self.timeout = 120  # 2 minutes timeout for API calls
        
        # Set up API endpoints based on provider
        if self.provider == "replicate":
            self.base_url = "https://api.replicate.com/v1/predictions"
            self.headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "together":
            self.base_url = "https://api.together.xyz/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "huggingface":
            self.base_url = f"https://api-inference.huggingface.co/models/{self.model}"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "github":
            self.base_url = os.getenv("GITHUB_API_BASE", "https://models.inference.ai.azure.com") + "/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        else:
            logger.warning(f"Unknown provider: {self.provider}, using mock responses")
            self.base_url = None
            self.headers = {}
        
        logger.info(f"🦙 Llama client initialized: {self.provider} provider with model {self.model}")
        
    def is_available(self) -> bool:
        """Check if Llama API is available and configured."""
        try:
            # Check if API key is configured
            if not self.api_key or self.api_key == "your_llama_api_key_here":
                logger.warning(f"Llama API key not configured for provider: {self.provider}")
                return False
                
            # Check if base URL is configured
            if not self.base_url:
                logger.warning(f"Llama base URL not configured for provider: {self.provider}")
                return False
            
            # For Replicate, we can check if the API is reachable
            if self.provider == "replicate":
                # Test API connectivity (this is optional)
                test_response = requests.get("https://api.replicate.com/v1/models", 
                                           headers=self.headers, timeout=10)
                return test_response.status_code in [200, 401]  # 401 means API key issue but service is up
            
            # For other providers, assume available if API key is set
            return True
            
        except Exception as e:
            logger.warning(f"Llama API not available: {e}")
            return False
    
    def generate_email(self, prompt: str) -> str:
        """
        Generate email content using Llama via API providers.
        
        Args:
            prompt: The prompt for email generation
            
        Returns:
            Generated email content
        """
        if not self.is_available():
            logger.error(f"Llama API ({self.provider}) not available")
            return self._fallback_response(prompt)
        
        try:
            logger.info(f"Generating email with Llama model: {self.model} via {self.provider}")
            start_time = time.time()
            
            if self.provider == "replicate":
                return self._generate_replicate(prompt, start_time)
            elif self.provider == "together":
                return self._generate_together(prompt, start_time)
            elif self.provider == "huggingface":
                return self._generate_huggingface(prompt, start_time)
            elif self.provider == "github":
                return self._generate_github(prompt, start_time)
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return self._fallback_response(prompt)
                
        except requests.exceptions.Timeout:
            logger.error(f"Llama generation timed out after {self.timeout} seconds")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Llama generation failed: {e}")
            return self._fallback_response(prompt)
    
    def _generate_replicate(self, prompt: str, start_time: float) -> str:
        """Generate using Replicate API."""
        payload = {
            "version": self.model,
            "input": {
                "prompt": prompt,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_length": 1000,
                "system_prompt": "You are a helpful assistant that generates professional, personalized emails."
            }
        }
        
        response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=self.timeout)
        
        if response.status_code == 201:
            prediction = response.json()
            prediction_url = prediction['urls']['get']
            
            # Poll for completion
            for _ in range(30):  # Max 30 polls (30 seconds)
                time.sleep(1)
                poll_response = requests.get(prediction_url, headers=self.headers)
                if poll_response.status_code == 200:
                    result = poll_response.json()
                    if result['status'] == 'succeeded':
                        output = ''.join(result['output']) if isinstance(result['output'], list) else result['output']
                        duration = time.time() - start_time
                        logger.info(f"Llama response generated in {duration:.2f}s")
                        return self._clean_response(output)
                    elif result['status'] == 'failed':
                        logger.error(f"Replicate prediction failed: {result.get('error', 'Unknown error')}")
                        return self._fallback_response(prompt)
            
            logger.error("Replicate prediction timed out")
            return self._fallback_response(prompt)
        else:
            logger.error(f"Replicate API error: {response.status_code} - {response.text}")
            return self._fallback_response(prompt)
    
    def _generate_together(self, prompt: str, start_time: float) -> str:
        """Generate using Together AI API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates professional, personalized emails."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000
        }
        
        response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=self.timeout)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            
            duration = time.time() - start_time
            logger.info(f"Llama response generated in {duration:.2f}s")
            return self._clean_response(generated_text)
        else:
            logger.error(f"Together AI API error: {response.status_code} - {response.text}")
            return self._fallback_response(prompt)
    
    def _generate_huggingface(self, prompt: str, start_time: float) -> str:
        """Generate using HuggingFace Inference API."""
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_new_tokens": 1000,
                "return_full_text": False
            }
        }
        
        response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=self.timeout)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result[0]['generated_text'] if isinstance(result, list) else result['generated_text']
            
            duration = time.time() - start_time
            logger.info(f"Llama response generated in {duration:.2f}s")
            return self._clean_response(generated_text)
        else:
            logger.error(f"HuggingFace API error: {response.status_code} - {response.text}")
            return self._fallback_response(prompt)
    
    def _generate_github(self, prompt: str, start_time: float) -> str:
        """Generate using GitHub Models API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates professional, personalized emails for academic research internship applications."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000
        }
        
        response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=self.timeout)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            
            duration = time.time() - start_time
            logger.info(f"GitHub Models response generated in {duration:.2f}s")
            return self._clean_response(generated_text)
        else:
            logger.error(f"GitHub Models API error: {response.status_code} - {response.text}")
            return self._fallback_response(prompt)
    
    def _clean_response(self, text: str) -> str:
        """Clean and format the generated response."""
        import re
        
        text = text.strip()
        
        # Remove email formatting artifacts (Subject:, Dear X:, etc)
        text = re.sub(r'^Subject:.*?\n\n', '', text, flags=re.MULTILINE | re.DOTALL)
        text = re.sub(r'^Dear Professor.*?,?\n\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Dear Prof\..*?,?\n\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n\nThank you.*$', '', text, flags=re.DOTALL)
        text = re.sub(r'\n\nBest regards,.*$', '', text, flags=re.DOTALL)
        text = re.sub(r'\n\nSincerely,.*$', '', text, flags=re.DOTALL)
        text = re.sub(r'\[Your.*?\]', '', text)
        
        # Remove XML/HTML tags except the ones we want
        text = re.sub(r'<(?!/?(?:p|strong|em)\b)[^>]*>', '', text)
        
        # Remove any markdown formatting that might interfere with HTML
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        # If text doesn't start with paragraph content, treat entire text as one paragraph
        if not text.startswith('<p>'):
            # Split into sentences and create paragraphs
            sentences = re.split(r'(?<=\.)\s+(?=[A-Z])', text)
            if len(sentences) > 3:
                # Group sentences into paragraphs
                para1 = ' '.join(sentences[:len(sentences)//2])
                para2 = ' '.join(sentences[len(sentences)//2:])
                return f"<p>{para1}</p>\n\n<p>{para2}</p>"
            else:
                return f"<p>{text}</p>"
        
        return text
    
    def _fallback_response(self, prompt: str) -> str:
        """
        Return empty string to let the main system handle fallback.
        This ensures the detailed backup template is used instead.
        """
        logger.info("Llama API unavailable, returning empty for main system fallback")
        return ""
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return basic performance metrics."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "available": self.is_available(),
            "timeout": self.timeout
        }


# Global client instance
_llama_client = None


def get_llama_client() -> LlamaClient:
    """Get or create global Llama client instance."""
    global _llama_client
    if _llama_client is None:
        _llama_client = LlamaClient()
    return _llama_client


def generate_with_llama(prompt: str) -> str:
    """
    Generate response using Llama client.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Generated response text
    """
    client = get_llama_client()
    try:
        return client.generate_email(prompt)
    except Exception as e:
        logger.error(f"Llama generation failed: {e}")
        return ""


# Test function
if __name__ == "__main__":
    # Test the Llama client
    test_prompt = """
    Generate a personalized email to Professor Smith at MIT about machine learning research.
    The email should be professional and show genuine interest in their work.
    """
    
    print("🦙 Testing Llama client...")
    client = LlamaClient()
    
    print(f"Provider: {client.provider}")
    print(f"Model: {client.model}")
    print(f"API Key configured: {'Yes' if client.api_key else 'No'}")
    
    if client.is_available():
        print("✅ Llama API is available")
        result = client.generate_email(test_prompt)
        print("\n📧 Generated email:")
        print("-" * 50)
        print(result)
        print("-" * 50)
    else:
        print("❌ Llama API not available - using fallback")
        result = client._fallback_response(test_prompt)
        print("\n📧 Fallback response:")
        print("-" * 50)
        print(result)
        print("-" * 50)
