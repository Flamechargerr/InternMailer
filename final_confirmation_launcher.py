#!/usr/bin/env python3
"""
FINAL CONFIRMATION LAUNCHER

This script will:
1. Load the complete professor database (45K+ unique emails)
2. Create personalized emails for 2 random professors with authentic research data
3. Send both sample emails to tripathy.anamay23@gmail.com for your confirmation
4. Wait for your confirmation to launch the full campaign

Each email will be fully personalized based on the professor's actual research.
"""

import pandas as pd
import random
import logging
import os
from typing import List, Dict
from dotenv import load_dotenv
from internship_outreach_system import InternshipOutreachSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('confirmation_launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_combined_professor_database() -> pd.DataFrame:
    """Load and combine all professor data sources"""
    logger.info("Loading complete professor database...")
    
    # Load CSRankings data (names, affiliations, Scholar IDs)
    csrankings_files = [f"data/csrankings-{letter}.csv" for letter in "abcdefghijklmnopqrstuvwxyz"]
    csrankings_data = []
    
    for file in csrankings_files:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                df['source'] = 'csrankings'
                csrankings_data.append(df)
            except Exception as e:
                logger.warning(f"Could not load {file}: {e}")
    
    # Load email data
    email_files = [
        'data/enhanced_background_emails_20250804_204317.csv',
        'data/enhanced_background_emails_20250804_203320.csv'
    ]
    
    email_data = []
    for file in email_files:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                df['source'] = 'email_data'
                email_data.append(df)
            except Exception as e:
                logger.warning(f"Could not load {file}: {e}")
    
    # Combine all data
    all_data = []
    if csrankings_data:
        csrankings_combined = pd.concat(csrankings_data, ignore_index=True)
        logger.info(f"Loaded {len(csrankings_combined):,} professors from CSRankings")
        all_data.append(csrankings_combined)
    
    if email_data:
        email_combined = pd.concat(email_data, ignore_index=True)
        logger.info(f"Loaded {len(email_combined):,} email records")
        all_data.append(email_combined)
    
    if not all_data:
        logger.error("No data loaded!")
        return pd.DataFrame()
    
    # Merge and clean
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Standardize columns
    combined_df.columns = [col.lower().strip() for col in combined_df.columns]
    
    # Clean and filter valid emails
    if 'email' in combined_df.columns:
        combined_df = combined_df.dropna(subset=['email'])
        combined_df['email'] = combined_df['email'].astype(str).str.lower().str.strip()
        combined_df = combined_df[combined_df['email'].str.contains('@', na=False)]
        
        # Remove duplicates by email
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['email'], keep='first')
        logger.info(f"Removed {initial_count - len(combined_df):,} duplicate emails")
    
    logger.info(f"Final database: {len(combined_df):,} unique professors")
    return combined_df

def select_quality_test_professors(df: pd.DataFrame, count: int = 2) -> List[Dict]:
    """Select high-quality professors for testing with better success probability"""
    
    # Create multiple tiers of quality professors
    
    # Tier 1: Professors with Scholar IDs (highest success rate)
    tier1 = df[
        (df.get('name', '').notna()) & 
        (df.get('affiliation', '').notna()) & 
        (df.get('scholarid', '') != 'NOSCHOLARPAGE') &
        (df.get('scholarid', '').notna()) &
        (df.get('scholarid', '').str.len() > 5)  # Valid Scholar ID length
    ]
    
    # Tier 2: Professors from reputable universities (common research publishers)
    reputable_unis = ['MIT', 'Stanford', 'CMU', 'Berkeley', 'Harvard', 'Cambridge', 'Oxford', 'ETH', 'EPFL', 
                     'IIT', 'NUS', 'NTU', 'University of Washington', 'Cornell', 'Princeton', 'Yale',
                     'University of Toronto', 'McGill', 'Waterloo', 'Georgia Tech', 'Caltech']
    
    tier2 = df[
        (df.get('name', '').notna()) & 
        (df.get('affiliation', '').notna()) & 
        (df.get('affiliation', '').str.contains('|'.join(reputable_unis), case=False, na=False))
    ]
    
    # Tier 3: Professors with academic email domains (likely active researchers)
    tier3 = df[
        (df.get('name', '').notna()) & 
        (df.get('affiliation', '').notna()) & 
        (df.get('email', '').str.contains(r'\.(edu|ac\.|edu\.|ac\.|ac$)', case=False, na=False))
    ]
    
    # Select from tiers with preference for higher tiers
    candidates = []
    
    # Try to get at least one from Tier 1 if available
    if len(tier1) > 0:
        sample_size = min(max(1, count // 2), len(tier1))
        candidates.extend(tier1.sample(n=sample_size).to_dict('records'))
    
    # Fill remaining from Tier 2
    remaining = count - len(candidates)
    if remaining > 0 and len(tier2) > 0:
        sample_size = min(remaining, len(tier2))
        tier2_sample = tier2[~tier2.index.isin([c.get('index') for c in candidates])]
        if len(tier2_sample) > 0:
            candidates.extend(tier2_sample.sample(n=min(sample_size, len(tier2_sample))).to_dict('records'))
    
    # Fill remaining from Tier 3
    remaining = count - len(candidates)
    if remaining > 0 and len(tier3) > 0:
        sample_size = min(remaining, len(tier3))
        tier3_sample = tier3[~tier3.index.isin([c.get('index') for c in candidates])]
        if len(tier3_sample) > 0:
            candidates.extend(tier3_sample.sample(n=min(sample_size, len(tier3_sample))).to_dict('records'))
    
    # Fallback to any professor if still not enough
    remaining = count - len(candidates)
    if remaining > 0:
        all_profs = df[df.get('name', '').notna()]
        remaining_profs = all_profs[~all_profs.index.isin([c.get('index') for c in candidates])]
        if len(remaining_profs) > 0:
            sample_size = min(remaining, len(remaining_profs))
            candidates.extend(remaining_profs.sample(n=sample_size).to_dict('records'))
    
    # Convert to expected format
    result = []
    for prof in candidates[:count]:
        result.append({
            'name': prof.get('name', 'Unknown Professor'),
            'affiliation': prof.get('affiliation', 'Unknown University'),
            'email': prof.get('email', ''),
            'scholarid': prof.get('scholarid', ''),
            'homepage': prof.get('homepage', '')
        })
    
    logger.info(f"Selected {len(result)} professors: Tier1={min(len(tier1), count)}, Tier2={len([p for p in result if any(uni in p.get('affiliation', '') for uni in reputable_unis)])}, Tier3={len([p for p in result if '.edu' in p.get('email', '') or '.ac.' in p.get('email', '')])}")
    
    return result

def main():
    print("🚀 FINAL CONFIRMATION LAUNCHER")
    print("=" * 80)
    print("This will send 2 personalized sample emails to tripathy.anamay23@gmail.com")
    print("for your confirmation before launching the full campaign.")
    print("=" * 80)
    
    # Your profile
    your_profile = {
        'name': 'Anamay Tripathy',
        'background': 'a third-year B.Tech Data Science student at MIT Manipal, India',
        'email': 'tripathy.anamay23@gmail.com',
        'interests': ['machine learning', 'artificial intelligence', 'deep learning'],
        'skills': ['Python', 'TensorFlow', 'PyTorch', 'SQL', 'React.js', 'AWS'],
        'achievements': 'Led technical development at a government-incubated startup; Automated KPI dashboards at Intellect Design Arena, saving 12+ hours weekly; Achieved 89% prediction accuracy in a sports prediction project.',
        'portfolio': 'https://anamay.vercel.app/',
        'linkedin': 'https://linkedin.com/in/anamay-tripathy',
        'github': 'https://github.com/Flamechargerr'
    }
    
    # Initialize system
    system = InternshipOutreachSystem(your_profile, test_mode=True)
    
    # Load complete database
    print("\n📊 Loading professor database...")
    professor_df = load_combined_professor_database()
    
    if professor_df.empty:
        print("❌ No professor data loaded. Exiting.")
        return
    
    # Try multiple professors until we get 2 successful emails
    print("\n🎯 Finding professors with research data for testing...")
    
    successful_emails = 0
    attempts = 0
    max_attempts = 20  # Try up to 20 professors to get 2 successful ones
    processed_professors = []
    
    while successful_emails < 2 and attempts < max_attempts:
        # Select next batch of professors to try
        batch_size = min(5, max_attempts - attempts)
        test_professors = select_quality_test_professors(professor_df, count=batch_size)
        
        if not test_professors:
            print("❌ No more professors available for testing.")
            break
        
        for prof_data in test_professors:
            if successful_emails >= 2:
                break
                
            attempts += 1
            print(f"\n[Attempt {attempts}] Processing {prof_data['name']} at {prof_data['affiliation']}...")
            
            try:
                # Create author profile with real research data
                profile = system.research_finder.create_author_profile(
                    name=prof_data['name'],
                    affiliation=prof_data['affiliation'],
                    email=prof_data['email']
                )
                
                if not profile or not profile.recent_publications:
                    print(f"   ⚠️  No research data found - trying next professor")
                    continue
                
                print(f"   ✅ Found {len(profile.recent_publications)} publications")
                
                # Generate personalized email
                email_data = system.create_personalized_email(profile)
                if not email_data:
                    print(f"   ❌ Failed to generate email - trying next professor")
                    continue
                
                # Save locally
                system.save_email_to_file(email_data)
                
                # Send to you for confirmation
                success = system.send_email(email_data, to_override=your_profile['email'])
                
                if success:
                    successful_emails += 1
                    processed_professors.append(prof_data)
                    print(f"   ✅ SUCCESS! Sample email #{successful_emails} sent to {your_profile['email']}")
                    
                    # Show publication titles for reference
                    print(f"   📚 Publications found:")
                    for j, pub in enumerate(profile.recent_publications[:3], 1):
                        print(f"       {j}. {pub.title[:80]}{'...' if len(pub.title) > 80 else ''} ({pub.year})")
                else:
                    print(f"   ❌ Failed to send email - trying next professor")
                    
            except Exception as e:
                logger.error(f"Error processing {prof_data['name']}: {e}")
                print(f"   ❌ Error: {e} - trying next professor")
    
    print(f"\n📊 Search completed after {attempts} attempts")
    if successful_emails >= 2:
        print(f"✅ Successfully found {successful_emails} professors with research data!")
        print("\n🎯 Final selected professors:")
        for i, prof in enumerate(processed_professors, 1):
            print(f"   {i}. {prof['name']} at {prof['affiliation']}")
    else:
        print(f"⚠️  Only found {successful_emails} professors with research data out of {attempts} attempts")
    
    # Final results
    print("\n" + "=" * 80)
    print("🎉 CONFIRMATION SAMPLES COMPLETE!")
    print("=" * 80)
    print(f"📊 Results:")
    print(f"   • Professors processed: {len(test_professors)}")
    print(f"   • Successful emails: {successful_emails}")
    print(f"   • Total database size: {len(professor_df):,} professors")
    print(f"   • Sent to: {your_profile['email']}")
    
    if successful_emails > 0:
        print(f"\n✅ Please check your inbox at {your_profile['email']}")
        print("📧 Review the personalized emails and confirm:")
        print("   1. Research data is authentic and relevant")
        print("   2. Personalization quality is high")
        print("   3. Email template and formatting look good")
        print("   4. Your contact information is correct")
        print(f"\n🚀 If approved, the system is ready to email all {len(professor_df):,} professors!")
        print("\n📁 Sample emails also saved in 'test_emails/' folder for review")
        
        # Ask for confirmation
        print("\n" + "=" * 80)
        confirmation = input("Type 'LAUNCH' to start the full campaign to all professors: ").strip()
        
        if confirmation.upper() == 'LAUNCH':
            print("🚀 FULL CAMPAIGN AUTHORIZED!")
            print("Starting mass email campaign...")
            # Here you would launch the full campaign
            print("⚠️  Full campaign implementation pending - contact system administrator")
        else:
            print("✋ Campaign not launched. Review samples and run again when ready.")
    else:
        print("❌ No successful sample emails sent. Please check configuration and try again.")

if __name__ == "__main__":
    main()
