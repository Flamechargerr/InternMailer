import streamlit as st
import os
import csv
import pandas as pd
from src.professor_scraper import ProfessorScraper

# --- App Configuration ---
st.set_page_config(
    page_title="Professor Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Main Application ---
def main():
    st.title("🔍 Professor Scraper")
    st.markdown("Automatically scrape professor data from CSRankings and enrich with contact information.")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Configuration")
        data_dir = st.text_input("Data Directory", "data")
        
        st.header("Actions")
        if st.button("Scrape Professors (Smart)"):
            scrape_professors_smart(data_dir)
        
        if st.button("Scrape Professors (Force All)"):
            scrape_professors(data_dir)
        
        if st.button("Merge All Professor Data"):
            merge_all_professor_data()
        
        st.header("Scraping Status")
        if os.path.exists(data_dir):
            scraper = ProfessorScraper(data_dir)
            scraped_summary = scraper.get_scraped_summary()
            st.metric("Professors Scraped", scraped_summary['total_professors_scraped'])
            st.metric("Emails Found", scraped_summary['total_emails_found'])
            st.metric("Success Rate", f"{scraped_summary['success_rate']}%")
            if st.button("Clear Professor Cache"):
                if os.path.exists(scraper.cache_file):
                    os.remove(scraper.cache_file)
                    st.success("Professor scraping cache cleared!")
        
        st.info("💡 Upload CSRankings CSV files to the data directory before scraping")

    # --- Main Content Area ---
    tab1, tab2 = st.tabs(["CSV Files", "Scraped Professors"])
    
    with tab1:
        st.header("Available CSV Files")
        display_csv_files(data_dir)
        
    with tab2:
        st.header("Scraped Professor Data")
        display_professor_data()

def scrape_professors_smart(data_dir):
    """Run the smart professor scraping pipeline (skips already scraped)"""
    if not os.path.exists(data_dir):
        st.error(f"Data directory '{data_dir}' not found!")
        return
        
    try:
        scraper = ProfessorScraper(data_dir)
        
        with st.spinner("Parsing CSV files..."):
            professors = scraper.parse_csvs()
            st.success(f"Found {len(professors)} professors in CSV files")
            
        unscraped_professors = scraper.get_unscraped_professors(professors)
        if not unscraped_professors:
            st.success("All professors have already been scraped!")
            st.json(scraper.get_scraped_summary())
            
            # Load existing data and update display
            with st.spinner("Loading cached results..."):
                enriched_professors = scraper.enrich_with_emails_smart()
                final_professors = scraper.deduplicate_and_filter()
                
                # Save to CSV
                output_file = os.path.join(data_dir, "scraped_professors.csv")
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    if final_professors:
                        fieldnames = final_professors[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(final_professors)
            return
        
        st.info(f"Found {len(unscraped_professors)} unscraped professors out of {len(professors)} total.")
            
        with st.spinner(f"Scraping email addresses from {len(unscraped_professors)} new homepages..."):
            progress_bar = st.progress(0)
            enriched_professors = scraper.enrich_with_emails_smart()
            st.success("Smart email scraping completed")
            
        with st.spinner("Deduplicating and filtering..."):
            final_professors = scraper.deduplicate_and_filter()
            st.success(f"Final dataset: {len(final_professors)} unique professors")
            
        # Save to CSV
        output_file = os.path.join(data_dir, "scraped_professors.csv")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if final_professors:
                fieldnames = final_professors[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(final_professors)
                
        st.success(f"✅ Smart scraping completed! Data saved to {output_file}")
        st.json(scraper.get_scraped_summary())
        
    except Exception as e:
        st.error(f"Smart scraping failed: {str(e)}")

def scrape_professors(data_dir):
    """Run the professor scraping pipeline (scrapes all, ignoring cache)"""
    if not os.path.exists(data_dir):
        st.error(f"Data directory '{data_dir}' not found!")
        return
        
    try:
        scraper = ProfessorScraper(data_dir)
        
        with st.spinner("Parsing CSV files..."):
            professors = scraper.parse_csvs()
            st.success(f"Found {len(professors)} professors in CSV files")
            
        with st.spinner("Scraping email addresses from homepages (forcing all)..."):
            enriched_professors = scraper.enrich_with_emails()
            st.success("Email scraping completed")
            
        with st.spinner("Deduplicating and filtering..."):
            final_professors = scraper.deduplicate_and_filter()
            st.success(f"Final dataset: {len(final_professors)} unique professors")
            
        # Save to CSV
        output_file = os.path.join(data_dir, "scraped_professors.csv")
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if final_professors:
                fieldnames = final_professors[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(final_professors)
                
        st.success(f"✅ Scraping completed! Data saved to {output_file}")
        
    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")

def display_csv_files(data_dir):
    """Display available CSV files in the data directory"""
    if not os.path.exists(data_dir):
        st.warning(f"Data directory '{data_dir}' not found")
        return
        
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        st.info("No CSV files found in the data directory")
        return
        
    for csv_file in csv_files:
        with st.expander(f"📄 {csv_file}"):
            try:
                df = pd.read_csv(os.path.join(data_dir, csv_file))
                st.dataframe(df.head(10))
                st.caption(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            except Exception as e:
                st.error(f"Error reading {csv_file}: {e}")

def display_professor_data():
    """Display scraped professor data"""
    scraped_file = "data/scraped_professors.csv"
    
    if not os.path.exists(scraped_file):
        st.info("No scraped professor data found. Run the scraper first!")
        return
        
    try:
        df = pd.read_csv(scraped_file)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Professors", len(df))
        with col2:
            professors_with_email = len(df[df['email'].notna() & (df['email'] != '')])
            st.metric("With Email", professors_with_email)
        with col3:
            email_rate = professors_with_email / len(df) * 100 if len(df) > 0 else 0
            st.metric("Email Success Rate", f"{email_rate:.1f}%")
        
        # Filters
        st.subheader("Filters")
        col1, col2 = st.columns(2)
        
        with col1:
            show_only_with_email = st.checkbox("Show only professors with email", value=True)
            
        with col2:
            if 'affiliation' in df.columns:
                selected_universities = st.multiselect(
                    "Filter by University",
                    options=df['affiliation'].unique().tolist(),
                    default=[]
                )
        
        # Apply filters
        filtered_df = df.copy()
        if show_only_with_email:
            filtered_df = filtered_df[filtered_df['email'].notna() & (filtered_df['email'] != '')]
            
        if 'affiliation' in df.columns and selected_universities:
            filtered_df = filtered_df[filtered_df['affiliation'].isin(selected_universities)]
        
        # Display data
        st.subheader(f"Professor Data ({len(filtered_df)} results)")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="filtered_professors.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error loading professor data: {e}")

def merge_all_professor_data():
    """Merge all professor data into a master file"""
    data_dir = "data"
    
    files_to_merge = [
        os.path.join(data_dir, "proffesor.csv"),
        os.path.join(data_dir, "scraped_professors.csv"),
        os.path.join(data_dir, "additional_professors.csv"),
    ]
    
    all_dfs = []
    for file in files_to_merge:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
                if not df.empty:
                    all_dfs.append(df)
                    st.info(f"Loaded {len(df)} professors from {os.path.basename(file)}")
            except Exception as e:
                st.error(f"Error reading {file}: {e}")
    
    if not all_dfs:
        st.error("No data to merge.")
        return
        
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Check if we have an Email column for deduplication
    if "Email" in merged_df.columns:
        original_count = len(merged_df)
        merged_df.drop_duplicates(subset=["Email"], keep="first", inplace=True)
        duplicates_removed = original_count - len(merged_df)
        st.info(f"Removed {duplicates_removed} duplicate entries")
    
    # Save to master file
    output_file = os.path.join(data_dir, "professors_master_list.csv")
    merged_df.to_csv(output_file, index=False)
    
    st.success(f"✅ Successfully merged {len(merged_df)} unique professors into {os.path.basename(output_file)}")
    
    # Option to update original file
    if st.button("Update Original Professor File"):
        original_file = os.path.join(data_dir, "proffesor.csv")
        backup_file = os.path.join(data_dir, "proffesor_backup.csv")
        
        # Create backup
        if os.path.exists(original_file):
            try:
                original_df = pd.read_csv(original_file, on_bad_lines='skip')
                original_df.to_csv(backup_file, index=False)
                st.info(f"Created backup: {os.path.basename(backup_file)}")
            except Exception as e:
                st.error(f"Could not create backup: {e}")
                return
        
        # Update original file
        merged_df.to_csv(original_file, index=False)
        st.success(f"✅ Updated {os.path.basename(original_file)} with merged data")

if __name__ == "__main__":
    main()
