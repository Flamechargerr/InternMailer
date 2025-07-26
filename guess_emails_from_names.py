import pandas as pd
import re

def clean_name(name):
    name = re.sub(r'[^a-zA-Z\s]', '', str(name))
    parts = name.strip().split()
    if len(parts) < 2:
        return '', ''
    first, last = parts[0], parts[-1]
    return first.lower(), last.lower()

def generate_email(first, last, domain):
    return [
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{last}@{domain}",
        f"{first}@{domain}"
    ]

# Load your CSV
df = pd.read_csv("InternMailer/data/qs_top50_professors.csv")

# Set the domain (e.g., mit.edu for MIT)
domain = "mit.edu"

emails = []
for i, row in df.iterrows():
    name = row.get("name") or row.get("Name")
    first, last = clean_name(name)
    if first and last:
        guesses = generate_email(first, last, domain)
        emails.append(guesses[0])  # Use the most common pattern
    else:
        emails.append("")

df["email_guess"] = emails
df.to_csv("InternMailer/data/qs_top50_professors_with_guessed_emails.csv", index=False)
print("Saved guessed emails to qs_top50_professors_with_guessed_emails.csv") 