#!/usr/bin/env python3
"""
📈 EXPAND HIRING LIST UTILITY
=============================
Helper script to add new hiring manager contacts to the database.
"""

import csv
import sys
from pathlib import Path
from typing import Optional

def add_contact(name: str, email: str, company: str, role: str, department: str, source: str = "Manual"):
    """📝 Add a new contact to the CSV file"""
    csv_path = Path(__file__).parent / 'data' / 'hiring_managers.csv'
    
    # Check if file exists, if not create with header
    file_exists = csv_path.exists()
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Name', 'Email', 'Company', 'Role', 'Department', 'Source'])
            
        writer.writerow([name, email, company, role, department, source])
        
    print(f"✅ Added contact: {name} ({company})")

def interactive_mode():
    """🗣️ Interactive mode to add contacts"""
    print("📈 ADD NEW HIRING MANAGER")
    print("=======================")
    
    while True:
        print("\nEnter contact details (or 'q' to quit):")
        name = input("Name: ").strip()
        if name.lower() == 'q':
            break
            
        email = input("Email: ").strip()
        company = input("Company: ").strip()
        role = input("Role (e.g. Hiring Manager): ").strip()
        department = input("Department (e.g. Engineering): ").strip()
        source = input("Source (optional, default: Manual): ").strip() or "Manual"
        
        if name and email and company:
            add_contact(name, email, company, role, department, source)
        else:
            print("❌ Name, Email, and Company are required!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode: python expand_hiring_list.py "Name" "Email" "Company" ...
        if len(sys.argv) >= 4:
            add_contact(
                sys.argv[1], 
                sys.argv[2], 
                sys.argv[3], 
                sys.argv[4] if len(sys.argv) > 4 else "Hiring Manager",
                sys.argv[5] if len(sys.argv) > 5 else "Engineering",
                "Command Line"
            )
        else:
            print("Usage: python expand_hiring_list.py <Name> <Email> <Company> [Role] [Department]")
    else:
        interactive_mode()
