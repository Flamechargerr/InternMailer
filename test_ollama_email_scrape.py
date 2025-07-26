import requests
import json
from bs4 import BeautifulSoup

def extract_email_with_ollama(homepage_url, ollama_url="http://localhost:11434/api/generate", ollama_model="gemma3"):
    try:
        resp = requests.get(homepage_url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        prompt = f"""
Extract all email addresses from the following webpage text. Return only a JSON list of emails.

Webpage text:
{text[:3000]}
"""
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False
        }
        llm_resp = requests.post(ollama_url, json=payload, timeout=60)
        llm_resp.raise_for_status()
        result = llm_resp.json().get("response", "")
        # Find the first valid JSON list in the response
        json_start = result.find('[')
        json_end = result.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            emails = json.loads(result[json_start:json_end])
            if emails and isinstance(emails, list):
                return emails
        return []
    except Exception as e:
        print(f"Ollama scraping failed for {homepage_url}: {e}")
        return []

# Test URLs (replace/add with real professor homepages)
test_urls = [
    "https://engineering.mit.edu/faculty-research/year",
    "http://adam.chlipala.net",
    "http://ssg.mit.edu/~willsky",
    "http://people.csail.mit.edu/meyer"
]

for url in test_urls:
    print(f"Testing {url} ...")
    emails = extract_email_with_ollama(url)
    print("Extracted emails:", emails)
    print("-" * 40) 