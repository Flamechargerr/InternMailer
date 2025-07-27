"""
Function: fetch_and_parse(country: str, top_n: int) -> List[{"name","affiliation","profile_url","domain","email"}]
 - Scrape CSRankings.org for Asia filtered by country
 - Validate & dedupe emails (email-validator)
 - Return top_n professors by ranking plus their personal Google Scholar or lab page URL
 - Save to data/professors.json
"""

import requests
from bs4 import BeautifulSoup
import json
from email_validator import validate_email, EmailNotValidError
from typing import List, Dict, Set
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import glob
import csv
from rapidfuzz import process, fuzz

def available_countries(region: str) -> List[str]:
    """
    Return a static list of countries for a given region.
    """
    if region.lower() == "asia":
        return [
            "India", "China", "Japan", "South Korea", "Singapore",
            "Hong Kong", "Taiwan", "Israel", "Turkey", "Pakistan"
        ]
    if region.lower() == "north america":
        return ["USA", "Canada", "Mexico"]
    return []

def _extract_email_from_homepage(url: str) -> str:
    """Try to extract an email address from a professor's homepage."""
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        email_regex = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        match = re.search(email_regex, soup.get_text())
        if match:
            return match.group(0)
    except Exception:
        pass
    return ""

def _scrape_professors(country: str, top_n: int) -> List[Dict]:
    """
    Use Selenium with Brave to scrape CSRankings.org for professors in the given country.
    Simulate clicks to expand 'All Areas' and select the country.
    Returns a list of professor dicts with name, affiliation, profile_url, domain, and email.
    """
    url = "https://csrankings.org/"
    profs = []
    try:
        chrome_options = Options()
        chrome_options.binary_location = r'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(
            executable_path=r'C:/Users/anama/OneDrive/Desktop/chromedriver-win64/chromedriver-win64/chromedriver.exe',
            options=chrome_options
        )
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        # 1. Expand 'All Areas'
        try:
            all_areas_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='all_areas_on']")))
            if not all_areas_btn.is_selected():
                all_areas_btn.click()
            time.sleep(1)
        except Exception as e:
            print(f"Could not expand 'All Areas': {e}")
        # 2. Select country from dropdown
        try:
            country_select = wait.until(EC.presence_of_element_located((By.ID, 'country')))
            for option in country_select.find_elements(By.TAG_NAME, 'option'):
                if country.lower() in option.text.lower():
                    option.click()
                    break
            time.sleep(2)
        except Exception as e:
            print(f"Could not select country: {e}")
        # 3. Wait for table to populate and scrape rows
        try:
            rows = driver.find_elements(By.XPATH, '//table[@id="csranking"]//tr')
            print(f"[DEBUG] Number of rows found: {len(rows)}")
            for i, row in enumerate(rows[:5]):
                print(f"[DEBUG] Row {i} text: {row.text}")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) < 2:
                    continue
                affiliation = cells[1].text.strip()
                if country.lower() not in affiliation.lower():
                    continue
                name_tag = cells[0].find_element(By.TAG_NAME, 'a')
                name = name_tag.text.strip()
                profile_url = name_tag.get_attribute('href')
                scholar_url = ''
                for a in cells[0].find_elements(By.TAG_NAME, 'a'):
                    href = a.get_attribute('href')
                    if 'scholar.google' in href:
                        scholar_url = href
                email = ''
                if profile_url:
                    email = _extract_email_from_homepage(profile_url)
                if not email and scholar_url:
                    email = _extract_email_from_homepage(scholar_url)
                domain = cells[2].text.strip() if len(cells) > 2 else ''
                profs.append({
                    "name": name,
                    "affiliation": affiliation,
                    "profile_url": profile_url or scholar_url,
                    "domain": domain,
                    "email": email
                })
                if len(profs) >= top_n:
                    break
        except Exception as e:
            print(f"Error scraping table rows: {e}")
        driver.quit()
        return profs
    except Exception as e:
        print(f"Error scraping CSRankings with Selenium for {country}: {e}")
        try:
            driver.quit()
        except Exception:
            pass
        return []

def _validate_and_dedupe(professors: List[Dict]) -> List[Dict]:
    """
    Validate and deduplicate professor emails using email-validator.
    """
    seen_emails: Set[str] = set()
    valid_professors: List[Dict] = []
    for prof in professors:
        try:
            if prof["email"]:
                v = validate_email(prof["email"])
                email = v.email
                if email not in seen_emails:
                    seen_emails.add(email)
                    valid_professors.append(prof)
        except (EmailNotValidError, KeyError, TypeError):
            continue
    return valid_professors

def fetch_and_parse(country: str, top_n: int) -> List[Dict]:
    """
    Scrape CSRankings.org for the selected country, validate emails, dedupe, and save top_n to data/professors.json
    """
    print(f"Fetching professors for {country} (top {top_n})...")
    professors = _scrape_professors(country, top_n)
    print(f"Scraped {len(professors)} raw professors.")
    valid_professors = _validate_and_dedupe(professors)
    print(f"{len(valid_professors)} professors after validation and deduplication.")
    valid_professors = valid_professors[:top_n]
    os.makedirs("data", exist_ok=True)
    with open("data/professors.json", "w", encoding="utf-8") as f:
        json.dump(valid_professors, f, indent=2)
    print(f"Saved {len(valid_professors)} professors to data/professors.json")
    return valid_professors

def parse_csv_professors(country: str, top_n: int) -> List[Dict]:
    """
    Parse all csrankings-[a-z].csv files in the data directory, filter by country using fuzzy matching with country-info.csv,
    validate and dedupe emails, and save top_n to data/professors.json.
    Returns the list of professor dicts.
    """
    # Load university-to-country mapping
    country_map = {}
    univ_list = []
    country_info_path = os.path.join('data', 'country-info.csv')
    if os.path.exists(country_info_path):
        import csv
        with open(country_info_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    univ, ctry = row[0].strip(), row[1].strip()
                    country_map[univ.lower()] = ctry.lower()
                    univ_list.append(univ)
    csv_files = sorted(glob.glob(os.path.join('data', 'csrankings-*.csv')))
    professors = []
    for csv_file in csv_files:
        with open(csv_file, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3:
                    continue
                name, affiliation, homepage = row[0].strip(), row[1].strip(), row[2].strip()
                # Fuzzy match affiliation to university list
                match, score, _ = process.extractOne(affiliation, univ_list, scorer=fuzz.ratio)
                if score < 90:
                    continue
                prof_country = country_map.get(match.lower(), None)
                if not prof_country or country.lower() != prof_country:
                    continue
                email = _extract_email_from_homepage(homepage) if homepage else ''
                prof = {
                    "name": name,
                    "affiliation": affiliation,
                    "profile_url": homepage,
                    "domain": "",
                    "email": email
                }
                professors.append(prof)
                if len(professors) >= top_n * 2:
                    break
        if len(professors) >= top_n * 2:
            break
    print(f"Parsed {len(professors)} professors from CSVs before validation.")
    valid_professors = _validate_and_dedupe(professors)
    print(f"{len(valid_professors)} professors after validation and deduplication.")
    valid_professors = valid_professors[:top_n]
    os.makedirs("data", exist_ok=True)
    with open("data/professors.json", "w", encoding="utf-8") as f:
        json.dump(valid_professors, f, indent=2)
    print(f"Saved {len(valid_professors)} professors to data/professors.json")
    return valid_professors
