#!/usr/bin/env python3
"""
Check the specific failed email address
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'InternMailer/src'))

from gmail_sender import GmailSender

def check_failed_email():
    """Check the specific email that failed"""
    print("Checking the failed email address: lvilanov@doc.ic.ac.uk")
    
    # Mock Gmail sender
    sender = GmailSender("test@example.com", "test_password")
    
    # Test the specific failed email
    failed_email = "lvilanov@doc.ic.ac.uk"
    
    print(f"Email: {failed_email}")
    print(f"Valid format: {sender.validate_email(failed_email)}")
    
    # Check each part of the email
    if '@' in failed_email:
        local, domain = failed_email.split('@')
        print(f"Local part: '{local}' (length: {len(local)})")
        print(f"Domain part: '{domain}' (length: {len(domain)})")
        print(f"Domain has TLD: {'.' in domain}")
    else:
        print("No @ symbol found")
    
    # Check against our CSV data
    import pandas as pd
    try:
        df = pd.read_csv('InternMailer/data/proffesor_verified_emails.csv')
        row = df[df['Email'] == failed_email]
        if not row.empty:
            print(f"Found in CSV: {row.iloc[0].to_dict()}")
        else:
            print("Not found in CSV")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    # Test some other potentially problematic emails
    test_emails = [
        "lvilanov@doc.ic.ac.uk",  # The failed one
        "ghobadi@mit.edu",        # A known good one
        "test@domain",            # Missing TLD
        "@domain.com",            # Missing local part
        "user@",                 # Missing domain
        "",                      # Empty
    ]
    
    print("\nTesting various email formats:")
    for email in test_emails:
        is_valid = sender.validate_email(email)
        print(f"  {email}: {'✅' if is_valid else '❌'}")

if __name__ == "__main__":
    check_failed_email() 