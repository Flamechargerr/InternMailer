import requests
from bs4 import BeautifulSoup
import re
import csv
from tqdm import tqdm

BASE_URL = "https://csrankings.org/"

response = requests.get(BASE_URL)
soup = BeautifulSoup(response.text, "html.parser")

faculty_tags = soup.find_all("a", class_="homepagelink")
professor_data = []
print(f"Total faculty links found: {len(faculty_tags)}")

def extract_email(url):
    try:
        r = requests.get(url, timeout=5)
        s = BeautifulSoup(r.text, 'html.parser')
        text = s.get_text()
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return emails[0] if emails else ""
    except:
        return ""

for tag in tqdm(faculty_tags):
    try:
        homepage_url = tag['href']
        name = tag.find_previous('span', class_='name').text
        affiliation = tag.find_previous('span', class_='affiliation').text
        email = extract_email(homepage_url)
        professor_data.append([name, affiliation, homepage_url, email])
    except Exception:
        continue

with open("InternMailer/data/csrankings_professors.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Affiliation", "Homepage", "Email"])
    writer.writerows(professor_data)

print(f"✅ Scraping complete! Total professors collected: {len(professor_data)}") 