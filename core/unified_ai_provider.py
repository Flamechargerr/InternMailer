"""
🚀 UNIFIED AI PROVIDER SYSTEM v3.0
==================================
Streamlined AI provider management with Groq as primary.
Eliminates template-like emails through deep personalization.

Features:
- Primary: Groq (fast, free tier, 1000+ TPM)
- Fallback 1: OpenRouter (free models available)
- Fallback 2: GitHub Models (if token available)
- Fallback 3: Local Ollama (if running)
- Smart caching and rate limit handling
"""

import os
import re
import json
import time
import random
import hashlib
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


@dataclass
class PersonalizationResult:
    """Result of AI personalization"""
    opening_hook: str
    connection_paragraph: str
    research_mention: str
    why_fit: str
    confidence: float
    provider_used: str
    generation_time_ms: int


class UnifiedAIProvider:
    """
    Unified AI provider with intelligent fallback chain.
    Groq is primary for speed and reliability.
    """
    
    def __init__(self):
        # API Keys
        self.groq_key = os.getenv('GROQ_API_KEY', '')
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        
        # Provider status
        self.provider_status = {
            'groq': {'available': bool(self.groq_key), 'last_error': None, 'success_count': 0},
            'openrouter': {'available': True, 'last_error': None, 'success_count': 0},  # Has free tier without key
            'github': {'available': bool(self.github_token), 'last_error': None, 'success_count': 0},
            'ollama': {'available': False, 'last_error': None, 'success_count': 0}  # Checked at runtime
        }
        
        # Cache for generated content (avoid regenerating for same professor)
        self._cache: Dict[str, Dict] = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Rate limiting
        self._request_times: List[datetime] = []
        self._max_requests_per_minute = 30  # Conservative for free tiers
        
        # Check Ollama availability
        self._check_ollama()
        
        print("🚀 Unified AI Provider initialized")
        print(f"   Groq: {'✅' if self.provider_status['groq']['available'] else '❌'}")
        print(f"   OpenRouter: {'✅' if self.provider_status['openrouter']['available'] else '❌'}")
        print(f"   GitHub Models: {'✅' if self.provider_status['github']['available'] else '❌'}")
        print(f"   Ollama: {'✅' if self.provider_status['ollama']['available'] else '❌'}")
    
    def _check_ollama(self):
        """Check if Ollama is running locally"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                self.provider_status['ollama']['available'] = True
        except:
            pass
    
    def _get_cache_key(self, professor_name: str, university: str, research_area: str) -> str:
        """Generate cache key for professor"""
        content = f"{professor_name}|{university}|{research_area}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if valid"""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if datetime.now() - entry['timestamp'] < timedelta(seconds=self._cache_ttl):
                return entry['data']
            else:
                del self._cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save result to cache"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def _rate_limit_check(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        # Remove entries older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < timedelta(minutes=1)]
        return len(self._request_times) < self._max_requests_per_minute
    
    def _wait_for_rate_limit(self):
        """Wait if rate limited"""
        while not self._rate_limit_check():
            time.sleep(1)
    
    def _call_groq(self, prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Call Groq API - Primary provider (fast, reliable)"""
        if not self.groq_key:
            return None
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",  # Best quality on free tier
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=15
            )
            
            if response.status_code == 200:
                self.provider_status['groq']['success_count'] += 1
                return response.json()['choices'][0]['message']['content'].strip()
            elif response.status_code == 429:
                self.provider_status['groq']['last_error'] = "Rate limited"
                print("   ⚠️ Groq rate limited, will try fallback")
            else:
                self.provider_status['groq']['last_error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            self.provider_status['groq']['last_error'] = str(e)
        
        return None
    
    def _call_openrouter(self, prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Call OpenRouter API - Fallback 1 (free models available)"""
        try:
            headers = {
                "Content-Type": "application/json",
                "HTTP-Referer": "https://internmailer.app",
                "X-Title": "InternMailer"
            }
            if self.openrouter_key:
                headers["Authorization"] = f"Bearer {self.openrouter_key}"
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "google/gemma-2-9b-it:free",  # Free tier
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=20
            )
            
            if response.status_code == 200:
                self.provider_status['openrouter']['success_count'] += 1
                return response.json()['choices'][0]['message']['content'].strip()
            elif response.status_code == 429:
                self.provider_status['openrouter']['last_error'] = "Rate limited"
            else:
                self.provider_status['openrouter']['last_error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            self.provider_status['openrouter']['last_error'] = str(e)
        
        return None
    
    def _call_github_models(self, prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Call GitHub Models API - Fallback 2"""
        if not self.github_token:
            return None
        
        try:
            response = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=15
            )
            
            if response.status_code == 200:
                self.provider_status['github']['success_count'] += 1
                return response.json()['choices'][0]['message']['content'].strip()
            elif response.status_code == 429:
                self.provider_status['github']['last_error'] = "Rate limited"
            else:
                self.provider_status['github']['last_error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            self.provider_status['github']['last_error'] = str(e)
        
        return None
    
    def _call_ollama(self, prompt: str, max_tokens: int = 400) -> Optional[str]:
        """Call local Ollama - Fallback 3 (slow but always available if running)"""
        if not self.provider_status['ollama']['available']:
            return None
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                self.provider_status['ollama']['success_count'] += 1
                return response.json().get('response', '').strip()
            else:
                self.provider_status['ollama']['last_error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            self.provider_status['ollama']['last_error'] = str(e)
        
        return None
    
    def generate_with_fallback(self, prompt: str, max_tokens: int = 400) -> Tuple[Optional[str], str]:
        """
        Generate text with automatic fallback chain.
        Returns (content, provider_used)
        """
        self._wait_for_rate_limit()
        self._request_times.append(datetime.now())
        
        providers = [
            ('groq', self._call_groq),
            ('openrouter', self._call_openrouter),
            ('github', self._call_github_models),
            ('ollama', self._call_ollama)
        ]
        
        for provider_name, provider_func in providers:
            if self.provider_status[provider_name]['available']:
                result = provider_func(prompt, max_tokens)
                if result:
                    return result, provider_name
        
        return None, "none"
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 1000):
        """
        Standard completion interface for agents.
        Returns a response object with 'content' attribute.
        """
        from dataclasses import dataclass
        
        @dataclass
        class CompletionResponse:
            content: str
            provider: str
        
        # Build full prompt with system prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        content, provider = self.generate_with_fallback(full_prompt, max_tokens)
        
        if content is None:
            content = "Error: Unable to generate response from any AI provider."
            provider = "none"
        
        return CompletionResponse(content=content, provider=provider)
    
    def generate_professor_personalization(
        self,
        professor_name: str,
        university: str,
        research_area: str,
        papers: Optional[List[Dict]] = None
    ) -> PersonalizationResult:
        """
        Generate deep personalization for professor emails.
        Creates unique, non-templated content.
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(professor_name, university, research_area)
        cached = self._get_from_cache(cache_key)
        if cached:
            return PersonalizationResult(
                opening_hook=cached['opening_hook'],
                connection_paragraph=cached['connection_paragraph'],
                research_mention=cached['research_mention'],
                why_fit=cached['why_fit'],
                confidence=0.95,
                provider_used='cache',
                generation_time_ms=0
            )
        
        # Build paper context if available
        paper_context = ""
        if papers and len(papers) > 0:
            paper_titles = [p.get('title', '') for p in papers[:2] if p.get('title')]
            if paper_titles:
                paper_context = f"Recent papers: {', '.join(paper_titles)}. "
        
        # ANTI-TEMPLATING: Randomize prompt style
        prompt_styles = [
            "academic", "enthusiastic", "technical", "curious", "professional"
        ]
        style = random.choice(prompt_styles)
        
        # Generate opening hook
        hook_prompt = f"""You are Anamay Tripathy, a Data Science student at MIT Manipal.
Write ONE sentence (max 25 words) to open an email to Professor {professor_name} at {university}.

Their work: {research_area}. {paper_context}

Style: {style}
Rules:
- Be specific about their research
- Show genuine interest
- NO generic phrases like "I am writing to" or "I hope this email finds you"
- Start with something engaging about THEIR work
- Output ONLY the sentence, nothing else"""
        
        opening_hook, provider = self.generate_with_fallback(hook_prompt, max_tokens=100)
        if not opening_hook:
            # Smart fallback based on research area
            opening_hook = self._generate_fallback_hook(research_area, professor_name)
        
        # Clean up hook
        opening_hook = self._clean_ai_output(opening_hook)
        
        # Generate connection paragraph
        connection_prompt = f"""Write 2-3 sentences connecting Anamay's background to Professor {professor_name}'s research in {research_area}.

Anamay's experience:
- Technical Head at YaanBarpe: Led ML-powered systems, 34% efficiency improvement
- Intellect Design Arena: Processed 2.3M daily transactions, Python/Kafka pipelines
- Projects: VARtificial Intelligence (89% accurate XGBoost), CrimeConnect (MERN dashboard)

{paper_context}

Rules:
- Connect specific skills to their research area
- Be natural, not forced
- NO "I am impressed by your work" - be more specific
- Output ONLY the sentences"""
        
        connection, provider2 = self.generate_with_fallback(connection_prompt, max_tokens=200)
        if not connection:
            connection = self._generate_fallback_connection(research_area)
        connection = self._clean_ai_output(connection)
        
        # Generate research mention
        research_prompt = f"""Write ONE specific sentence mentioning Professor {professor_name}'s research in {research_area}.
{paper_context}

Rules:
- Mention a specific aspect of their field
- Use varied language (avoid "your work on")
- Be technical but accessible
- Output ONLY the sentence"""
        
        research_mention, provider3 = self.generate_with_fallback(research_prompt, max_tokens=100)
        if not research_mention:
            research_mention = f"your research contributions to {research_area}"
        research_mention = self._clean_ai_output(research_mention)
        
        # Generate why fit
        why_fit_prompt = f"""Write 1-2 sentences explaining why Anamay would be a good fit for Professor {professor_name}'s lab.

Research area: {research_area}
Anamay's skills: Python, PyTorch, TensorFlow, SQL, scalable ML pipelines, data visualization

Rules:
- Connect specific skills to their needs
- Show readiness to contribute
- Be confident but not arrogant
- Output ONLY the sentences"""
        
        why_fit, provider4 = self.generate_with_fallback(why_fit_prompt, max_tokens=150)
        if not why_fit:
            why_fit = self._generate_fallback_why_fit(research_area)
        why_fit = self._clean_ai_output(why_fit)
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        # Cache result
        result_data = {
            'opening_hook': opening_hook,
            'connection_paragraph': connection,
            'research_mention': research_mention,
            'why_fit': why_fit
        }
        self._save_to_cache(cache_key, result_data)
        
        # Determine primary provider used
        providers_used = [p for p in [provider, provider2, provider3, provider4] if p != 'none']
        primary_provider = providers_used[0] if providers_used else 'fallback'
        
        return PersonalizationResult(
            opening_hook=opening_hook,
            connection_paragraph=connection,
            research_mention=research_mention,
            why_fit=why_fit,
            confidence=0.9 if primary_provider != 'fallback' else 0.7,
            provider_used=primary_provider,
            generation_time_ms=generation_time_ms
        )

    def generate_role_personalization(
        self,
        contact_name: str,
        company: str,
        role: str,
        candidate_background: str = "",
        uniqueness_seed: str = "",
    ) -> PersonalizationResult:
        """
        Generate personalization for job application emails (non-academic).
        Avoids professor/research phrasing and invented company specifics.
        """
        start_time = time.time()

        # Include uniqueness seed in cache key if provided
        cache_content = f"{contact_name}|{company}|{role}_role"
        if uniqueness_seed:
            cache_content += f"|{uniqueness_seed}"
        
        cache_key = hashlib.md5(cache_content.encode()).hexdigest()
        cached = self._get_from_cache(cache_key)
        if cached:
            return PersonalizationResult(
                opening_hook=cached['opening_hook'],
                connection_paragraph=cached['connection_paragraph'],
                research_mention=cached['research_mention'],
                why_fit=cached['why_fit'],
                confidence=0.95,
                provider_used='cache',
                generation_time_ms=0
            )

        safe_company = company or "your company"
        safe_role = role or "the role"
        candidate_context = candidate_background or "Experience in software engineering, data systems, and automation."

        prompt_styles = ["professional", "concise", "technical", "direct", "enthusiastic", "analytical"]
        
        # Use uniqueness seed to determine style for consistency
        if uniqueness_seed:
            # Deterministic style based on seed
            seed_hash = hash(uniqueness_seed) % len(prompt_styles)
            style = prompt_styles[seed_hash]
        else:
            style = random.choice(prompt_styles)

        hook_prompt = f"""You are Anamay Tripathy, a software/data student applying for {safe_role}.
Write ONE sentence (max 25 words) to open an email to {contact_name} at {safe_company}.

Style: {style}
Rules:
- Focus on the role or team, not academics
- NO 'Professor', 'research', 'lab', 'papers', or faculty language
- Do NOT invent specific company details
- Avoid 'I am writing to' or 'I hope this email finds you'
- Output ONLY the sentence"""

        def sanitize_role_text(text: str, fallback: str) -> str:
            cleaned = self._clean_ai_output(text)
            cleaned = re.sub(r"\bprofessor\b", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\bprof\.?\b", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\blab\b", "team", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\bresearch\b", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"^i'm the\s+", "The ", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"^i am the\s+", "The ", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\.{2,}", ".", cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if not cleaned:
                return fallback
            return cleaned

        opening_hook, provider = self.generate_with_fallback(hook_prompt, max_tokens=80)
        opening_fallback = f"I'm excited about the opportunity to contribute to {safe_company} in a {safe_role} role."
        opening_hook = sanitize_role_text(opening_hook or "", opening_fallback)

        connection_prompt = f"""Write 2-3 sentences connecting Anamay's background to a {safe_role} role at {safe_company}.
Candidate background: {candidate_context}
Rules:
- Keep it professional and role-focused
- No professor/research language
- Do NOT invent company-specific facts
- Output ONLY the sentences"""

        connection, provider2 = self.generate_with_fallback(connection_prompt, max_tokens=200)
        connection_fallback = f"My background in software systems and data pipelines aligns well with {safe_role} responsibilities."
        connection = sanitize_role_text(connection or "", connection_fallback)

        interest_prompt = f"""Write ONE sentence about why the {safe_role} opportunity at {safe_company} is compelling.
Rules:
- Generic is fine; do NOT invent facts
- No professor/research language
- Output ONLY the sentence"""

        interest, provider3 = self.generate_with_fallback(interest_prompt, max_tokens=80)
        interest_fallback = f"I'm especially interested in applying my skills to the {safe_role} opportunity at {safe_company}."
        interest = sanitize_role_text(interest or "", interest_fallback)

        why_fit_prompt = f"""Write ONE sentence on why Anamay is a strong fit for {safe_role}.
Candidate background: {candidate_context}
Rules:
- Specific to skills/experience
- No professor/research language
- Output ONLY the sentence"""

        why_fit, provider4 = self.generate_with_fallback(why_fit_prompt, max_tokens=80)
        why_fit_fallback = "My experience building data-driven systems and production workflows would translate well to this role."
        why_fit = sanitize_role_text(why_fit or "", why_fit_fallback)

        generation_time_ms = int((time.time() - start_time) * 1000)

        providers_used = [p for p in [provider, provider2, provider3, provider4] if p != 'none']
        primary_provider = providers_used[0] if providers_used else 'fallback'

        result_data = {
            'opening_hook': opening_hook,
            'connection_paragraph': connection,
            'research_mention': interest,
            'why_fit': why_fit
        }
        self._save_to_cache(cache_key, result_data)

        return PersonalizationResult(
            opening_hook=opening_hook,
            connection_paragraph=connection,
            research_mention=interest,
            why_fit=why_fit,
            confidence=0.9 if primary_provider != 'fallback' else 0.7,
            provider_used=primary_provider,
            generation_time_ms=generation_time_ms
        )
    
    def _clean_ai_output(self, text: str) -> str:
        """Clean up AI-generated text"""
        if not text:
            return ""
        
        # Remove meta-commentary
        text = re.sub(r'^(Here is|Here are|Here\'s|Below is|Following is).*?:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(Opening|Connection|Research mention|Why fit).*?:', '', text, flags=re.IGNORECASE)
        
        # Remove quotes
        text = text.strip().strip('"').strip("'")
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _generate_fallback_hook(self, research_area: str, professor_name: str) -> str:
        """Generate fallback hook when AI fails"""
        hooks = [
            f"Your research on {research_area} represents exactly the kind of innovative work I'm eager to contribute to.",
            f"I've been following developments in {research_area} and your group's contributions stand out as particularly impactful.",
            f"The approach your lab takes to {research_area} aligns perfectly with my research interests and technical background.",
            f"Your group's work advancing {research_area} methodology is precisely the research direction I want to pursue.",
        ]
        # Deterministic selection based on professor name
        idx = hash(professor_name) % len(hooks)
        return hooks[idx]
    
    def _generate_fallback_connection(self, research_area: str) -> str:
        """Generate fallback connection when AI fails"""
        area_lower = research_area.lower()
        
        if any(kw in area_lower for kw in ['data', 'system', 'cloud', 'database']):
            return "My experience optimizing data pipelines at Intellect Design Arena—processing 2.3M daily transactions—gave me practical insights into scalable systems that directly applies to your research domain."
        elif any(kw in area_lower for kw in ['vision', 'image', 'video']):
            return "Building AI-driven systems like Flora Fight Frenzy taught me how to implement and optimize computer vision models, skills I'm eager to apply to your research."
        elif any(kw in area_lower for kw in ['ml', 'learning', 'ai', 'neural']):
            return "Developing VARtificial Intelligence—an XGBoost predictor achieving 89% accuracy—gave me hands-on experience with the machine learning techniques central to your work."
        elif any(kw in area_lower for kw in ['security', 'privacy']):
            return "My HackOps cybersecurity platform project demonstrated my ability to build secure, production-ready systems that align with your security research."
        else:
            return "My background in building production-grade ML systems and scalable data pipelines has prepared me to contribute meaningfully to your research group."
    
    def _generate_fallback_why_fit(self, research_area: str) -> str:
        """Generate fallback why_fit when AI fails"""
        return "I bring strong Python and ML skills, experience with production systems, and genuine enthusiasm for contributing to cutting-edge research in your lab."
    
    def get_provider_stats(self) -> Dict:
        """Get statistics on provider usage"""
        return {
            'status': self.provider_status,
            'cache_size': len(self._cache),
            'requests_last_minute': len(self._request_times)
        }


# Global instance
_ai_provider = None

def get_unified_ai_provider() -> UnifiedAIProvider:
    """Get singleton instance of UnifiedAIProvider"""
    global _ai_provider
    if _ai_provider is None:
        _ai_provider = UnifiedAIProvider()
    return _ai_provider


if __name__ == "__main__":
    # Test the provider
    provider = get_unified_ai_provider()
    
    print("\n" + "="*60)
    print("Testing Professor Personalization")
    print("="*60)
    
    result = provider.generate_professor_personalization(
        professor_name="Dr. Sarah Chen",
        university="Stanford University",
        research_area="Computer Vision and Deep Learning",
        papers=[{"title": "Advanced Object Detection in Autonomous Systems"}]
    )
    
    print(f"\nOpening Hook: {result.opening_hook}")
    print(f"\nConnection: {result.connection_paragraph}")
    print(f"\nResearch Mention: {result.research_mention}")
    print(f"\nWhy Fit: {result.why_fit}")
    print(f"\nProvider: {result.provider_used}")
    print(f"Time: {result.generation_time_ms}ms")
    print(f"Confidence: {result.confidence}")
