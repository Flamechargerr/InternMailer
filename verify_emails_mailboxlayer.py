import requests
import pandas as pd

API_KEY = "1274ead969408765231f90da2ee30ca3"
df = pd.read_csv("InternMailer/data/proffesor.csv")

def verify_email(email):
    url = f"http://apilayer.net/api/check?access_key={API_KEY}&email={email}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return data.get("format_valid") and data.get("smtp_check")
    except:
        return False

# Only check emails that look like emails
mask = df["Email"].astype(str).str.contains("@")
df.loc[mask, "email_valid"] = df.loc[mask, "Email"].apply(verify_email)
df.loc[~mask, "email_valid"] = False

df.to_csv("InternMailer/data/proffesor_verified_emails.csv", index=False)
print("Saved verified emails to proffesor_verified_emails.csv") 