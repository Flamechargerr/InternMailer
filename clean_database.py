#!/usr/bin/env python3
"""
Database Cleaning Script
========================
Fixes contaminated email addresses in the professor database
"""

import pandas as pd
import re
import os

def clean_email_address(email):
    """Clean and validate email addresses"""
    if pd.isna(email) or not isinstance(email, str):
        return None
    
    email = str(email).strip().lower()
    
    # Remove common contaminations
    contaminations = [
        'phone', 'fax', 'office', 'room', 'building', 'address',
        'professor', 'dr.', 'phd', 'http://', 'https://', 'www.',
        '.html', '.php', '.aspx', '.open', '.pdf', '.doc', '.txt',
        'mailto:', '<', '>', '"', "'", '(', ')', '[', ']'
    ]
    
    for contamination in contaminations:
        if contamination in email:
            # Try to extract just the email part
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4})'
            match = re.search(email_pattern, email)
            if match:
                email = match.group(1)
                break
            else:
                return None
    
    # Final validation - strict email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'
    if re.match(email_pattern, email):
        # Check for academic domains
        academic_domains = ['.edu', '.ac.', '.uni-', '.univ-']
        if any(domain in email for domain in academic_domains):
            # Additional check: email should not end with contamination
            if not any(cont in email.split('@')[0] or cont in email.split('@')[1] 
                      for cont in ['phone', 'open', 'fax', 'office', 'room', 'address']):
                # Validate TLD is proper (not contaminated)
                tld = email.split('.')[-1]
                if len(tld) >= 2 and len(tld) <= 4 and tld.isalpha():
                    return email
    
    return None

def main():
    """Clean the professor database"""
    print("🧹 Database Cleaning Script")
    print("=" * 40)
    
    db_path = 'production/databases/FINAL_MASTER_EMAIL_DATABASE.csv'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"📁 Loading database: {db_path}")
    df = pd.read_csv(db_path)
    original_count = len(df)
    print(f"📊 Original records: {original_count}")
    
    # Clean email addresses
    print("🧼 Cleaning email addresses...")
    df['email_clean'] = df['email'].apply(clean_email_address)
    
    # Remove records with invalid emails
    df_clean = df[df['email_clean'].notna()].copy()
    df_clean['email'] = df_clean['email_clean']
    df_clean = df_clean.drop('email_clean', axis=1)
    
    # Remove duplicates
    df_clean = df_clean.drop_duplicates(subset=['email'])
    
    clean_count = len(df_clean)
    removed_count = original_count - clean_count
    
    print(f"✅ Cleaning complete:")
    print(f"   - Original records: {original_count}")
    print(f"   - Clean records: {clean_count}")
    print(f"   - Removed: {removed_count}")
    print(f"   - Success rate: {(clean_count/original_count)*100:.1f}%")
    
    # Save cleaned database
    clean_db_path = 'production/databases/CLEANED_MASTER_EMAIL_DATABASE.csv'
    df_clean.to_csv(clean_db_path, index=False)
    print(f"💾 Saved clean database: {clean_db_path}")
    
    # Show examples of cleaned emails
    print("\n📧 Sample of cleaned emails:")
    for i, email in enumerate(df_clean['email'].head(10)):
        print(f"   {i+1}. {email}")
    
    # Show examples of removed contaminated emails
    df_contaminated = df[df['email_clean'].isna()]
    if len(df_contaminated) > 0:
        print("\n🗑️ Sample of removed contaminated emails:")
        for i, email in enumerate(df_contaminated['email'].head(5)):
            print(f"   {i+1}. {email}")

if __name__ == "__main__":
    main()
