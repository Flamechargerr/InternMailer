#!/usr/bin/env python3
"""
Script to trim the professors CSV file starting after Barbara Liskov's row.
This script finds the row containing liskov@csail.mit.edu, drops that row and 
all previous rows, then saves the trimmed list as professors_next.csv.
"""

import pandas as pd
import sys

def trim_professors_csv():
    # Read the existing CSV file
    input_file = "data/proffesor.csv"
    output_file = "professors_next.csv"
    
    try:
        # Read the CSV file with error handling for malformed lines
        df = pd.read_csv(input_file, on_bad_lines='warn')
        
        print(f"Original CSV has {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Find the row containing liskov@csail.mit.edu
        liskov_mask = df['Email'].str.contains('liskov@csail.mit.edu', na=False)
        liskov_indices = df[liskov_mask].index
        
        if len(liskov_indices) == 0:
            print("ERROR: Could not find liskov@csail.mit.edu in the data")
            return False
            
        liskov_index = liskov_indices[0]
        print(f"Found Barbara Liskov at row index {liskov_index} (row {liskov_index + 2} in file including header)")
        print(f"Liskov row data: {df.iloc[liskov_index]['Name']} - {df.iloc[liskov_index]['Email']}")
        
        # Drop the Liskov row and all previous rows (keep rows after Liskov)
        trimmed_df = df.iloc[liskov_index + 1:].copy()
        
        print(f"Trimmed CSV will have {len(trimmed_df)} rows (starting after Barbara Liskov)")
        
        if len(trimmed_df) > 0:
            print(f"First professor in trimmed list: {trimmed_df.iloc[0]['Name']} - {trimmed_df.iloc[0]['Email']}")
        
        # Save the trimmed list
        trimmed_df.to_csv(output_file, index=False)
        print(f"Successfully saved trimmed list to {output_file}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = trim_professors_csv()
    sys.exit(0 if success else 1)
