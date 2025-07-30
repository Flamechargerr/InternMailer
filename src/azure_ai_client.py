"""
Azure AI client for OpenAI GPT-4.1 integration.
Replaces Ollama for faster and more reliable LLM operations.
"""

import os
import logging
import time
import hashlib
import random
import signal
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential
    AZURE_AI_AVAILABLE = True
except ImportError:
    # Fallback if Azure AI SDK is not installed
    ChatCompletionsClient = None
    SystemMessage = None
    UserMessage = None
    AzureKeyCredential = None
    AZURE_AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureAIClient:
    """
    Azure AI client for OpenAI GPT-4.1 integration.
    Provides faster and more reliable responses than local Ollama.
    """
    
    def __init__(self, endpoint: str = "https://models.inference.ai.azure.com", model: str = "gpt-4o"):
        # Ensure environment variables are loaded first
        from dotenv import load_dotenv
        load_dotenv()
        
        self.endpoint = endpoint
        self.model = model
        self.cache = {}  # Cache for identical prompts
        
        # Get API key from environment
        self.api_key = os.getenv("GITHUB_TOKEN")
        if not self.api_key or self.api_key == "your_github_token_here":
            logger.warning("GITHUB_TOKEN not configured, Azure AI will use mock responses")
            self.api_key = None
        
        # Initialize client
        if AZURE_AI_AVAILABLE and ChatCompletionsClient and self.api_key:
            try:
                self.client = ChatCompletionsClient(
                    endpoint=self.endpoint,
                    credential=AzureKeyCredential(self.api_key)
                )
                logger.info("✅ Azure AI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure AI client: {e}")
                self.client = None
        else:
            self.client = None
            if not AZURE_AI_AVAILABLE:
                logger.info("ℹ️ Azure AI SDK not available, using fallback mode for development")
            elif not self.api_key:
                logger.info("ℹ️ Azure AI API key not configured, using mock responses for development")
    
    def generate_with_fallback(self, prompt: str, model: str = None) -> str:
        """
        Generate response with Azure AI, using cache when possible.
        
        Args:
            prompt: The prompt to send to the model
            model: Model name (optional, uses default if not provided)
            
        Returns:
            Generated response text
        """
        # Use provided model or default
        model_name = model or self.model
        
        # Check cache first
        cache_key = hashlib.md5(f"{prompt}_{model_name}".encode()).hexdigest()
        if cache_key in self.cache:
            logger.info("Using cached response")
            return self.cache[cache_key]
        
        if not self.client:
            logger.error("Azure AI client not available")
            return ""
        
        # Retry logic with exponential backoff for rate limiting
        max_retries = 5
        base_delay = 1
        max_delay = 60
        
        # Simple single attempt - fail fast and return empty for any error
        try:
            start_time = time.time()
            logger.info(f"Generating response with Azure AI {model_name}")
            
            # Create messages for chat completion
            messages = [
                SystemMessage(content="You are a helpful assistant that generates professional, concise responses."),
                UserMessage(content=prompt)
            ]
            
            # Make API call - any error will be caught and return empty
            response = self.client.complete(
                messages=messages,
                model=model_name,
                temperature=0.7,
                max_tokens=1000,
            )
            
            # Extract response text
            if response.choices and len(response.choices) > 0:
                result = response.choices[0].message.content
                
                # Cache the result
                self.cache[cache_key] = result
                
                duration = time.time() - start_time
                logger.info(f"Azure AI response generated in {duration:.2f}s")
                
                return result
            else:
                logger.error("No response choices returned from Azure AI")
                return ""
                
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Azure AI failed: {e}")
            logger.info("Returning empty string to trigger backup template")
            return ""  # Return empty string to trigger fallback
        
        # If we get here, all retries failed
        logger.error(f"Azure AI generation failed after {max_retries} attempts")
        return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """
        Provide a mock response when Azure AI is not available.
        This is for development/testing purposes.
        """
        if "email" in prompt.lower() and "professor" in prompt.lower():
            # Extract professor name from prompt if possible
            prof_name = "Professor"
            if "Prof." in prompt:
                try:
                    prof_name = prompt.split("Prof.")[1].split("at")[0].strip()
                except:
                    prof_name = "Professor"
            
            return f"""Dear {prof_name},

I hope this email finds you well. My name is Anamay Tripathy, and I am a B.Tech Data Science student at MIT Manipal, India.

I am writing to express my interest in potential research opportunities within your group. Your work in the field has caught my attention, and I would be honored to contribute to your research efforts as an intern.

I have experience with Python, machine learning, and web development through various projects including CrimeConnect and VARtificial Intelligence. Currently, I serve as Technical Head at YaanBarpe, a government-incubated startup.

I would be grateful for the opportunity to discuss potential research internship positions, whether remote or on-site, for Winter 2025 or Summer 2026.

Thank you for your time and consideration. Please find my CV attached.

Best regards,
Anamay Tripathy
B.Tech Data Science | MIT Manipal, India
Email: tripathy.anamay23@gmail.com"""
        elif "resume" in prompt.lower() or "skills" in prompt.lower():
            return '''
            {
                "skills": ["Python", "JavaScript", "React", "Node.js", "Machine Learning"],
                "projects": ["CrimeConnect", "VARtificial Intelligence"],
                "courses": ["Data Structures", "Machine Learning", "Web Development"],
                "experience": ["Technical Intern at Intellect Design Arena"],
                "summary": "Technical professional with experience in Python, JavaScript, and Machine Learning",
                "domains": ["Data Science", "Web Development"]
            }
            '''
        else:
            return "Mock response - Azure AI client not properly configured"
    
    def is_available(self) -> bool:
        """Check if Azure AI client is available and configured."""
        return self.client is not None and self.api_key is not None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return basic performance metrics."""
        return {
            "cache_size": len(self.cache),
            "endpoint": self.endpoint,
            "model": self.model,
            "available": self.is_available()
        }


# Global client instance
_azure_ai_client = None


def get_azure_ai_client() -> AzureAIClient:
    """Get or create global Azure AI client instance."""
    global _azure_ai_client
    if _azure_ai_client is None:
        _azure_ai_client = AzureAIClient()
    return _azure_ai_client


def generate_with_azure_ai(prompt: str, model: str = "gpt-4o") -> str:
    """
    Generate response using Azure AI client.
    
    Args:
        prompt: The prompt to send to the model
        model: Model name to use
        
    Returns:
        Generated response text
    """
    client = get_azure_ai_client()
    try:
        return client.generate_with_fallback(prompt, model)
    except Exception as e:
        logger.error(f"Azure AI generation failed: {e}")
        return ""
