"""
Azure AI client for OpenAI GPT-4.1 integration.
Replaces Ollama for faster and more reliable LLM operations.
"""

import os
import logging
import time
import hashlib
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
    
    def __init__(self, endpoint: str = "https://models.github.ai/inference", model: str = "openai/gpt-4.1"):
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
                logger.info("ℹ️ Azure AI SDK available but using fallback mode for development")
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
            return self._mock_response(prompt)
        
        try:
            start_time = time.time()
            logger.info(f"Generating response with Azure AI {model_name}")
            
            # Create messages for chat completion
            messages = [
                SystemMessage(content="You are a helpful assistant that generates professional, concise responses."),
                UserMessage(content=prompt)
            ]
            
            # Make API call
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
            logger.error(f"Azure AI generation failed: {e}")
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """
        Provide a mock response when Azure AI is not available.
        This is for development/testing purposes.
        """
        if "resume" in prompt.lower() or "skills" in prompt.lower():
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


def generate_with_azure_ai(prompt: str, model: str = "openai/gpt-4.1") -> str:
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
