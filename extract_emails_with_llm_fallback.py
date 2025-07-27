import pandas as pd
import re
import requests
import json
from bs4 import BeautifulSoup

def extract_email_regex(url):
    try:
        resp = requests.get(url, timeout=5)
        match = re.search(r"[\w\.-]+@[\w\.-]+", resp.text)
        return match.group(0) if match else ''
    except:
        return ''

def extract_email_with_ollama(url, ollama_url="http://localhost:11434/api/generate", ollama_model="gemma3"):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Use shorter, more focused prompt for email extraction
        prompt = f"""
Find email addresses in this webpage text. Return only a JSON array of emails.

Text (first 2000 chars):
{text[:2000]}

Return: ["email1@domain.com", "email2@domain.com"]
"""
        
        # Import enhanced client
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'InternMailer', 'src'))
        
        try:
            from email_generator import get_ollama_client
            client = get_ollama_client()
            result = client.generate_with_fallback(prompt, ollama_model)
        except ImportError:
            # Fallback to original method if enhanced client not available
            payload = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False
            }
            llm_resp = requests.post(ollama_url, json=payload, timeout=120)  # Increased timeout
            llm_resp.raise_for_status()
            result = llm_resp.json().get("response", "")
        
        if not result:
            return ''
            
        json_start = result.find('[')
        json_end = result.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            emails = json.loads(result[json_start:json_end])
            if emails and isinstance(emails, list):
                return emails[0] if emails else ''
        return ''
    except Exception as e:
        print(f"Ollama scraping failed for {url}: {e}")
        return ''

# Load original data
df = pd.read_csv("InternMailer/data/qs_top50_professors.csv")

# Add homepage column, move URLs into it if needed
if 'homepage' not in df.columns:
    df["homepage"] = df["email"]

# Extract real emails from homepage URLs using regex, then LLM fallback
emails = []
for i, row in df.iterrows():
    url = row.get('homepage', '')
    email = ''
    if isinstance(url, str) and url.startswith('http'):
        email = extract_email_regex(url)
        if not email:
            print(f"Regex failed for {url}, trying LLM fallback...")
            email = extract_email_with_ollama(url)
    emails.append(email)
    print(f"Row {i}: {email}")

df["email"] = emails

df.to_csv("InternMailer/data/qs_professors_with_emails.csv", index=False)
print("Saved to InternMailer/data/qs_professors_with_emails.csv") 