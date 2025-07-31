import pandas as pd
import os

def merge_professor_data():
    """Merges all professor data into a single master file."""
    data_dir = "data"
    
    # List of files to merge
    files_to_merge = [
        os.path.join(data_dir, "proffesor.csv"),
        os.path.join(data_dir, "scraped_professors.csv"),
        os.path.join(data_dir, "additional_professors.csv"),
    ]
    
    # Read and concatenate all dataframes
    all_dfs = []
    for file in files_to_merge:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
                if not df.empty:
                    all_dfs.append(df)
                    print(f"Loaded {len(df)} professors from {file}")
            except Exception as e:
                print(f"Error reading {file}: {e}")
    
    if not all_dfs:
        print("No data to merge.")
        return
        
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Deduplicate by email address
    merged_df.drop_duplicates(subset=["Email"], keep="first", inplace=True)
    
    # Save to master file
    output_file = os.path.join(data_dir, "professors_master_list.csv")
    merged_df.to_csv(output_file, index=False)
    
    print(f"Successfully merged {len(merged_df)} unique professors into {output_file}")

if __name__ == "__main__":
    merge_professor_data()
