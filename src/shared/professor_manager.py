"""
Centralized Professor Management
Handles loading, filtering, and searching professor data for the InternMailer application
"""

import streamlit as st
import pandas as pd
import os
from typing import Dict, List, Optional
from .config_manager import config_manager

class ProfessorManager:
    """Centralized professor data management"""
    
    def __init__(self):
        self.df = self._load_professors()
        
    @st.cache_data
    def _load_professors(_self) -> pd.DataFrame:
        """Load professor data with caching and error handling"""
        try:
            csv_path = config_manager.get_config('professor_csv_path')
            if not csv_path or not os.path.exists(csv_path):
                st.error("❌ Professor database not found")
                return pd.DataFrame()
            
            # Read CSV with error handling for malformed lines
            df = pd.read_csv(csv_path, on_bad_lines='skip', encoding='utf-8')
            
            # Handle different CSV formats
            if len(df.columns) == 5 and df.columns[0] != 'University':
                df.columns = ['University', 'Name', 'Email', 'Homepage', 'Research Area']
            
            # Clean the data
            df = df.dropna(subset=['Email'])  # Remove rows with missing emails
            df = df[df['Email'].str.contains('@', na=False)]  # Only keep valid email formats
            df = df[df['University'] != 'University']  # Remove duplicate headers
            df = df[df['Email'] != 'Email']  # Remove duplicate headers
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Clean and standardize column names
            df.columns = df.columns.str.strip()
            
            # Ensure required columns exist
            required_columns = ['Name', 'Email', 'University', 'Research Area']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            st.success(f"✅ Loaded {len(df)} professors from database")
            return df
            
        except FileNotFoundError:
            st.error("❌ Professor database not found")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Error loading professor database: {e}")
            return pd.DataFrame()
    
    def get_professors(self) -> pd.DataFrame:
        """Get the professor dataframe"""
        return self.df
    
    def is_available(self) -> bool:
        """Check if professor data is available"""
        return not self.df.empty
    
    def search_and_filter(self, 
                         search_term: str = "",
                         university: str = "All",
                         research_area: str = "All",
                         country: str = "All") -> pd.DataFrame:
        """Apply search and filters to professor data"""
        
        if self.df.empty:
            return pd.DataFrame()
        
        filtered_df = self.df.copy()
        
        # Apply text search
        if search_term:
            search_mask = (
                filtered_df['Name'].str.contains(search_term, case=False, na=False) |
                filtered_df['University'].str.contains(search_term, case=False, na=False) |
                filtered_df['Research Area'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]
        
        # Apply university filter
        if university != "All":
            filtered_df = filtered_df[filtered_df['University'] == university]
        
        # Apply research area filter
        if research_area != "All":
            filtered_df = filtered_df[filtered_df['Research Area'] == research_area]
        
        # Apply country filter (if column exists)
        if 'Country' in filtered_df.columns and country != "All":
            filtered_df = filtered_df[filtered_df['Country'] == country]
        
        return filtered_df
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options"""
        if self.df.empty:
            return {
                'universities': ['All'],
                'research_areas': ['All'],
                'countries': ['All']
            }
        
        options = {
            'universities': ['All'] + sorted(self.df['University'].dropna().unique().tolist()),
            'research_areas': ['All'] + sorted(self.df['Research Area'].dropna().unique().tolist()),
        }
        
        # Add countries if column exists
        if 'Country' in self.df.columns:
            options['countries'] = ['All'] + sorted(self.df['Country'].dropna().unique().tolist())
        else:
            options['countries'] = ['All']
        
        return options
    
    def create_search_interface(self) -> Dict[str, str]:
        """Create Streamlit search and filter interface"""
        st.header("🔍 Search & Filter Professors")
        
        # Get filter options
        options = self.get_filter_options()
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input(
                "🔍 Search professors by name, university, or research area",
                placeholder="e.g., Andrew Ng, Stanford, Machine Learning",
                help="Enter keywords to search across professor names, universities, and research areas"
            )
            
            university_filter = st.selectbox(
                "🏫 Filter by University",
                options=options['universities']
            )
        
        with col2:
            research_area_filter = st.selectbox(
                "🔬 Filter by Research Area",
                options=options['research_areas']
            )
            
            country_filter = st.selectbox(
                "🌍 Filter by Country",
                options=options['countries']
            )
        
        return {
            'search_term': search_term,
            'university': university_filter,
            'research_area': research_area_filter,
            'country': country_filter
        }
    
    def display_professor_card(self, professor_data, show_select_button=False, key_suffix=""):
        """Display a professor card with consistent formatting"""
        with st.container():
            st.markdown(f"""
            <div class="professor-card">
                <h3>👨‍🎓 {professor_data.get('Name', 'Unknown')}</h3>
                <p><strong>🏫 University:</strong> {professor_data.get('University', 'Unknown')}</p>
                <p><strong>🔬 Research Area:</strong> {professor_data.get('Research Area', 'Unknown')}</p>
                <p><strong>📧 Email:</strong> {professor_data.get('Email', 'Unknown')}</p>
                <p><strong>🌐 Homepage:</strong> <a href="{professor_data.get('Homepage', '#')}" target="_blank">{professor_data.get('Homepage', 'Not available')}</a></p>
            </div>
            """, unsafe_allow_html=True)
            
            if show_select_button:
                return st.button(f"✉️ Send Email to {professor_data.get('Name', 'Professor')}", 
                               key=f"select_{key_suffix}")
        
        return False

# Global professor manager instance
professor_manager = ProfessorManager()
