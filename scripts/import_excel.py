import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#!/usr/bin/env python3
"""
Import Excel file with Talent Acquisition contacts
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

def import_excel_recruiters(excel_path, db_path='data/recruiters.db'):
    """Import recruiters from Excel file"""
    
    if not os.path.exists(excel_path):
        print(f"❌ File not found: {excel_path}")
        return 0
    
    print(f"📄 Reading Excel: {excel_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        print(f"   Found {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        
        # Common column name mappings
        column_mappings = {
            'name': ['Name', 'Full Name', 'FullName', 'Contact Name', 'Person Name'],
            'first_name': ['First Name', 'FirstName', 'First'],
            'last_name': ['Last Name', 'LastName', 'Last'],
            'email': ['Email', 'Work Email', 'Email Address', 'Contact Email', 'Primary Email'],
            'company': ['Company', 'Organization', 'Company Name', 'Employer', 'Current Company'],
            'title': ['Title', 'Job Title', 'Position', 'Role', 'Designation'],
            'linkedin': ['LinkedIn', 'LinkedIn URL', 'Profile URL', 'LinkedIn Profile'],
            'location': ['Location', 'City', 'Country', 'Region']
        }
        
        # Find matching columns
        def find_column(df, possible_names):
            for name in possible_names:
                for col in df.columns:
                    if name.lower() in col.lower():
                        return col
            return None
        
        col_name = find_column(df, column_mappings['name'])
        col_first = find_column(df, column_mappings['first_name'])
        col_last = find_column(df, column_mappings['last_name'])
        col_email = find_column(df, column_mappings['email'])
        col_company = find_column(df, column_mappings['company'])
        col_title = find_column(df, column_mappings['title'])
        col_linkedin = find_column(df, column_mappings['linkedin'])
        col_location = find_column(df, column_mappings['location'])
        
        print(f"\n   Column mapping:")
        print(f"   Name: {col_name or col_first}")
        print(f"   Email: {col_email}")
        print(f"   Company: {col_company}")
        print(f"   Title: {col_title}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                email TEXT UNIQUE,
                title TEXT,
                company TEXT,
                industry TEXT,
                linkedin_url TEXT,
                location TEXT,
                source TEXT DEFAULT 'excel',
                imported_at TEXT,
                contacted TEXT DEFAULT 'no',
                verified TEXT DEFAULT 'no'
            )
        """)
        
        imported = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            try:
                # Get values
                if col_name:
                    full_name = str(row[col_name]).strip() if pd.notna(row[col_name]) else ''
                    parts = full_name.split()
                    first_name = parts[0] if parts else ''
                    last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                else:
                    first_name = str(row[col_first]).strip() if col_first and pd.notna(row[col_first]) else ''
                    last_name = str(row[col_last]).strip() if col_last and pd.notna(row[col_last]) else ''
                    full_name = f"{first_name} {last_name}".strip()
                
                email = str(row[col_email]).strip().lower() if col_email and pd.notna(row[col_email]) else ''
                company = str(row[col_company]).strip() if col_company and pd.notna(row[col_company]) else ''
                title = str(row[col_title]).strip() if col_title and pd.notna(row[col_title]) else 'Recruiter'
                linkedin = str(row[col_linkedin]).strip() if col_linkedin and pd.notna(row[col_linkedin]) else ''
                location = str(row[col_location]).strip() if col_location and pd.notna(row[col_location]) else ''
                
                # Validate email
                if not email or '@' not in email or email == 'nan':
                    skipped += 1
                    continue
                
                # Clean up name if empty
                if not full_name or full_name == 'nan':
                    full_name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
                    parts = full_name.split()
                    first_name = parts[0] if parts else ''
                    last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                
                # Insert
                cursor.execute("""
                    INSERT OR IGNORE INTO recruiters 
                    (first_name, last_name, full_name, email, title, company, linkedin_url, location, source, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'excel', ?)
                """, (first_name, last_name, full_name, email, title, company, linkedin, location, datetime.now().isoformat()))
                
                if cursor.rowcount > 0:
                    imported += 1
                    
            except Exception as e:
                skipped += 1
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Imported: {imported}")
        print(f"⏭️ Skipped (invalid/duplicate): {skipped}")
        
        return imported
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = r"C:\Users\anama\OneDrive\Desktop\New folder\data\_1800+ Talent Acquisition Database .xlsx"
    
    import_excel_recruiters(excel_path)
    
    # Show stats
    conn = sqlite3.connect('data/recruiters.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recruiters")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT company, COUNT(*) as cnt FROM recruiters GROUP BY company ORDER BY cnt DESC LIMIT 10")
    companies = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 TOTAL RECRUITERS: {total}")
    print("\n🏢 Top Companies:")
    for company, count in companies:
        print(f"   {company}: {count}")
