import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from rapidfuzz import process, fuzz

# ---------- STEP 1: Match affiliation to country ----------
def infer_country(affil, university_country_df):
    match = process.extractOne(affil, university_country_df['university'], scorer=fuzz.token_set_ratio)
    if match and match[1] >= 90:
        return university_country_df.loc[match[2], 'country']
    return None

# ---------- STEP 2: Load CSVs and apply country filter ----------
def load_data(target_country=None):
    dfs = []
    for c in 'abcdefghijklmnopqrstuvwxyz':
        path = f'csrankings-{c}.csv'  # Feel free to adjust path if different
        if Path(path).exists():
            df = pd.read_csv(path, usecols=['name', 'affiliation', 'homepage'])
            dfs.append(df)

    if not dfs:
        raise FileNotFoundError("❌ No CSRankings CSV files found (csrankings-a.csv … csrankings-z.csv).")

    full_df = pd.concat(dfs, ignore_index=True)

    if target_country:
        print(f"[🌍] Filtering professors by country: {target_country}")
        country_df = pd.read_csv("country-info.csv")

        # Validate column names
        required_cols = {'university', 'country'}
        if not required_cols.issubset(country_df.columns):
            raise KeyError(f"[❌] country-info.csv must contain columns: {required_cols}")

        full_df['country'] = full_df['affiliation'].apply(lambda x: infer_country(x, country_df))
        full_df = full_df[full_df['country'] == target_country]
        print(f"[✅] Professors found in {target_country}: {len(full_df)}")

    return full_df

# ---------- STEP 3: Extract email from homepage ----------
def extract_email(homepage_url):
    try:
        resp = requests.get(homepage_url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text()
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        for e in emails:
            if not any(ext in e for ext in ['.png', '.jpg', '@csrankings.org']):
                return e
    except:
        return ""
    return ""

# ---------- STEP 4: Guess research field from text ----------
def guess_field_from_homepage(text):
    text = text.lower()
    if 'machine learning' in text or 'deep learning' in text:
        return 'ML'
    elif 'computer vision' in text:
        return 'CV'
    elif 'natural language' in text or 'nlp' in text:
        return 'NLP'
    elif 'network' in text:
        return 'Networks'
    return 'General'

# ---------- STEP 5: Build professor list for ProfMailer ----------
def build_profmailer_list(df, max_rows=1000, target_field=None):
    records = []
    print(f"[🔍] Scraping homepages and building list (max {max_rows})...")

    for row in tqdm(df.itertuples(), total=len(df)):
        if len(records) >= max_rows:
            break

        name, affil, homepage = row.name, row.affiliation, row.homepage
        if not isinstance(homepage, str) or not homepage.startswith("http"):
            continue

        email = extract_email(homepage)
        if not email:
            continue

        # Optional: extract homepage text to guess research field
        try:
            resp = requests.get(homepage, timeout=10)
            homepage_text = BeautifulSoup(resp.text, 'html.parser').get_text()
        except:
            homepage_text = ""

        field = guess_field_from_homepage(homepage_text)
        if target_field and field != target_field:
            continue

        record = {
            "name": name.strip().split()[-1] if name else "",
            "email": email,
            "university": affil,
            "send_status": 0,
            "subject": "Prospective Graduate Student",
            "transcript": "False",
            "field": field,
            "group": "none"
        }
        records.append(record)

    print(f"[📫] Final professor count: {len(records)}")
    return pd.DataFrame(records)

# ---------- STEP 6: Run main ----------
if __name__ == '__main__':
    # ✅ Customize these parameters
    TARGET_COUNTRY = "India"  # Example: "United States", "Germany", "India", etc.
    TARGET_FIELD = "ML"       # Can be: ML, CV, NLP, Networks, General, or None
    MAX_PROFESSORS = 1000     # Stop after this many profs with valid emails

    print("\n[🚀] Starting InternMailer Extraction...\n")
    df = load_data(target_country=TARGET_COUNTRY)
    result = build_profmailer_list(df, max_rows=MAX_PROFESSORS, target_field=TARGET_FIELD)

    result.to_csv("list.csv", index=False)
    print("\n[✅] Successfully saved to list.csv — ready for ProfMailer!\n")
