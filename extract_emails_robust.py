import pandas as pd
import requests
import re
import json
from bs4 import BeautifulSoup
from tqdm import tqdm

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
        json_start = result.find('[')
        json_end = result.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            emails = json.loads(result[json_start:json_end])
            if emails and isinstance(emails, list):
                return emails[0]
        return ''
    except Exception as e:
        print(f"Ollama scraping failed for {url}: {e}", flush=True)
        return ''

def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", email))

# Load data
df = pd.read_csv("InternMailer/data/qs_top50_professors.csv")

# Auto-detect homepage column (case-insensitive)
homepage_col = None
for col in df.columns:
    if col.strip().lower() in ["homepage", "homepage url", "url"]:
        homepage_col = col
        break
if homepage_col is None:
    raise ValueError("No homepage column found in CSV.")

# Only keep rows with a homepage URL
df = df[df[homepage_col].astype(str).str.startswith("http")].reset_index(drop=True)

emails = []
for i, row in tqdm(df.iterrows(), total=len(df)):
    url = row[homepage_col]
    email = extract_email_regex(url)
    if not is_valid_email(email):
        print(f"Regex failed for {url}, trying LLM fallback...", flush=True)
        email = extract_email_with_ollama(url)
    if not is_valid_email(email):
        email = ''
    emails.append(email)
    print(f"Row {i}: {email}", flush=True)
    # Save every 100 rows for progress
    if (i+1) % 100 == 0:
        df_partial = df.iloc[:i+1].copy()
        df_partial["Email"] = emails
        df_valid = df_partial[df_partial["Email"] != ""]
        df_valid.to_csv("InternMailer/data/qs_top50_professors_partial.csv", index=False)
        print(f"Saved {len(df_valid)} valid emails so far...", flush=True)

# Assign emails to the full DataFrame
df["Email"] = emails
df_valid = df[df["Email"] != ""]
df_valid.to_csv("InternMailer/data/qs_top50_professors_with_emails.csv", index=False)
print(f"Saved {len(df_valid)} valid emails to InternMailer/data/qs_top50_professors_with_emails.csv") 