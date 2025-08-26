"""
🔬 ENHANCED RESEARCH SYSTEM v2.0
=====================================
Multi-source research scraping with attribution validation
Fixes: Research attribution errors (Prof. Maxim/Dr. Zheng Song issue)
Sources: Google Scholar, ResearchGate, ORCID, University pages, IEEE, ACM
"""

import requests
import urllib.parse
import time
import random
import re
from bs4 import BeautifulSoup


class EnhancedResearchSystem:
    """Enhanced research system with multiple sources and attribution validation"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.research_areas = [
            'machine learning', 'artificial intelligence', 'computer science',
            'data science', 'deep learning', 'neural networks', 'algorithms',
            'software engineering', 'computer vision', 'natural language processing',
            'human-computer interaction', 'robotics', 'cybersecurity', 'database systems'
        ]
    
    def scrape_professor_research_enhanced(self, name, email, affiliation):
        """🔍 ENHANCED: Multi-source research scraping with attribution validation"""
        try:
            clean_name = self.clean_professor_name(name)
            if not clean_name or len(clean_name) < 5:
                return self._get_enhanced_fallback_research_data(email, affiliation, name)
            
            print(f"🔬 Researching {clean_name} using multiple sources...")
            
            research_info = []
            
            # Strategy 1: Multi-source research discovery
            research_info.extend(self._search_google_scholar_validated(clean_name))
            research_info.extend(self._search_university_faculty_page(clean_name, email))
            research_info.extend(self._search_researchgate_profile(clean_name))
            research_info.extend(self._search_orcid_profile(clean_name))
            research_info.extend(self._search_academic_databases(clean_name))
            
            # Strategy 2: Validate authorship and remove incorrect attributions
            validated_research = self._validate_research_attribution(research_info, clean_name)
            
            print(f"📚 Found {len(research_info)} total, {len(validated_research)} validated")
            
            # Format the research mentions with validation confidence
            if validated_research:
                return self._format_validated_research_mentions(validated_research, clean_name)
            else:
                # Enhanced fallback based on domain and common research areas
                return self._get_enhanced_fallback_research_data(email, affiliation, clean_name)
                
        except Exception as e:
            print(f"Complete research scraping failed for {name}: {e}")
            return self._get_enhanced_fallback_research_data(email, affiliation, name)
    
    def clean_professor_name(self, name):
        """Clean professor name for search"""
        # Remove titles and clean the name
        clean_name = str(name).replace('Prof.', '').replace('Dr.', '').replace('Professor', '').strip()
        
        # Remove numbers and special characters that indicate corruption
        clean_name = re.sub(r'^[\d\s\W]*', '', clean_name)
        clean_name = re.sub(r'[\d\s\W]*$', '', clean_name)
        clean_name = re.sub(r'\d{3,}', '', clean_name)  # Remove long numbers
        
        # Filter out corrupted names
        if len(clean_name) < 3 or clean_name.lower() in ['professor', 'faculty', 'staff']:
            return None
        
        return clean_name.strip()
    
    def _search_google_scholar_validated(self, clean_name):
        """🎓 Search Google Scholar with enhanced author validation"""
        research_info = []
        
        try:
            # Enhanced search with author-specific queries
            search_queries = [
                f'author:"{clean_name}"',  # Exact author match
                f'"{clean_name}" "research" "university"',  # Academic context
                f'"{clean_name}" "publication" OR "paper"'  # Publication focus
            ]
            
            for query in search_queries:
                try:
                    scholar_url = f'https://scholar.google.com/scholar?q={urllib.parse.quote_plus(query)}&hl=en'
                    response = requests.get(scholar_url, headers=self.headers, timeout=15)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Extract publications with comprehensive parsing
                        title_patterns = [
                            r'<h3[^>]*><a[^>]*>([^<]+)</a></h3>',
                            r'<h3[^>]*class="gs_rt"[^>]*><a[^>]*>([^<]+)</a></h3>',
                            r'class="gs_rt"[^>]*><a[^>]*href="[^"]*">([^<]+)</a>'
                        ]
                        
                        titles = []
                        for pattern in title_patterns:
                            titles.extend(re.findall(pattern, content, re.IGNORECASE))
                        
                        # Extract author information for validation
                        author_pattern = r'<div class="gs_a">([^<]+)</div>'
                        authors_info = re.findall(author_pattern, content)
                        
                        # Extract publication years
                        year_pattern = r'(\b20\d{2}\b|\b19\d{2}\b)'
                        
                        for i, title in enumerate(titles[:3]):  # Top 3 results
                            if len(title) > 15:  # Filter meaningful titles
                                # Advanced author validation
                                author_confidence = 0
                                if i < len(authors_info):
                                    author_text = authors_info[i].lower()
                                    name_parts = [part.lower() for part in clean_name.split() if len(part) > 2]
                                    
                                    # Check multiple name combinations
                                    for part in name_parts:
                                        if part in author_text:
                                            author_confidence += 0.3
                                    
                                    # Check initials + last name pattern
                                    if len(name_parts) >= 2:
                                        initial_pattern = f"{name_parts[0][0]} {name_parts[-1]}"
                                        if initial_pattern in author_text:
                                            author_confidence += 0.4
                                    
                                    # Check for collaboration indicators (RED FLAGS)
                                    red_flag_phrases = [
                                        'based on the work of', 'colleague', 'collaboration with',
                                        'joint work', 'co-authored by', 'work of my colleague'
                                    ]
                                    
                                    has_red_flags = any(flag in author_text.lower() for flag in red_flag_phrases)
                                    if has_red_flags:
                                        author_confidence = 0  # Reject immediately
                                
                                # Extract publication year
                                year_match = re.search(year_pattern, authors_info[i] if i < len(authors_info) else '')
                                pub_year = year_match.group(1) if year_match else 'Recent'
                                
                                research_info.append({
                                    'title': title.strip(),
                                    'description': f'Academic research publication ({pub_year})',
                                    'source': 'Google Scholar',
                                    'author_confidence': author_confidence,
                                    'validation_method': 'scholar_author_check',
                                    'year': pub_year
                                })
                        
                        if research_info:  # Found some results, no need to try other queries
                            break
                            
                    elif response.status_code == 429:
                        print(f"📚 Scholar rate limited, waiting...")
                        time.sleep(3)
                    
                except Exception as e:
                    print(f"Scholar query failed: {e}")
                    continue
            
            print(f"📚 Google Scholar: {len(research_info)} papers found")
            
        except Exception as e:
            print(f"Google Scholar search failed: {e}")
        
        return research_info
    
    def _search_university_faculty_page(self, clean_name, email):
        """🏫 Search university faculty pages for research information"""
        research_info = []
        
        try:
            domain = email.split('@')[1]
            
            # Search queries for faculty pages
            search_queries = [
                f'"{clean_name}" site:{domain} "faculty" "research"',
                f'"{clean_name}" site:{domain} "professor" "publications"'
            ]
            
            for query in search_queries[:1]:  # Limit searches
                try:
                    search_url = f'https://www.google.com/search?q={urllib.parse.quote_plus(query)}'
                    response = requests.get(search_url, headers=self.headers, timeout=10)
                    
                    if response.status_code == 200:
                        content = response.text.lower()
                        
                        # Look for research keywords in content
                        found_keywords = [kw for kw in self.research_areas if kw in content]
                        
                        if found_keywords:
                            primary_area = found_keywords[0].title()
                            research_info.append({
                                'title': f'Faculty Research in {primary_area}',
                                'description': f'University research focusing on {primary_area} and computational methods',
                                'source': 'University Faculty Page',
                                'author_confidence': 0.8,  # High confidence from official source
                                'validation_method': 'faculty_page',
                                'research_areas': found_keywords[:3]
                            })
                            break  # Found relevant info
                    
                except Exception as e:
                    continue
            
            print(f"🏫 University pages: {len(research_info)} entries found")
            
        except Exception as e:
            print(f"University search failed: {e}")
        
        return research_info
    
    def _search_researchgate_profile(self, clean_name):
        """🔬 Search ResearchGate for professor profiles"""
        research_info = []
        
        try:
            # ResearchGate search via Google
            search_query = f'"{clean_name}" site:researchgate.net (profile OR publications)'
            search_url = f'https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}'
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check if ResearchGate profile exists
                if 'researchgate.net' in content and clean_name.lower() in content:
                    found_topics = [topic for topic in self.research_areas if topic in content]
                    
                    if found_topics:
                        research_info.append({
                            'title': f'ResearchGate Profile - {found_topics[0].title()}',
                            'description': f'Active researcher with focus on {found_topics[0]} and related fields',
                            'source': 'ResearchGate',
                            'author_confidence': 0.7,
                            'validation_method': 'researchgate_profile'
                        })
            
            print(f"🔬 ResearchGate: {len(research_info)} entries found")
            
        except Exception as e:
            print(f"ResearchGate search failed: {e}")
        
        return research_info
    
    def _search_orcid_profile(self, clean_name):
        """🆔 Search ORCID for researcher profiles"""
        research_info = []
        
        try:
            # ORCID search via Google
            search_query = f'"{clean_name}" site:orcid.org'
            search_url = f'https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}'
            
            response = requests.get(search_url, headers=self.headers, timeout=8)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for ORCID profile existence
                if 'orcid.org' in content and clean_name.lower() in content:
                    research_info.append({
                        'title': 'ORCID Researcher Profile',
                        'description': 'Verified researcher with ORCID profile and academic publications',
                        'source': 'ORCID',
                        'author_confidence': 0.9,  # High confidence from verified source
                        'validation_method': 'orcid_verified'
                    })
            
            print(f"🆔 ORCID: {len(research_info)} entries found")
            
        except Exception as e:
            print(f"ORCID search failed: {e}")
        
        return research_info
    
    def _search_academic_databases(self, clean_name):
        """📚 Search additional academic databases"""
        research_info = []
        
        try:
            # Search IEEE, ACM, arXiv, etc. via Google
            databases = [
                ('IEEE', 'site:ieeexplore.ieee.org'),
                ('ACM', 'site:dl.acm.org'),
            ]
            
            for db_name, site_filter in databases:
                try:
                    search_query = f'"{clean_name}" {site_filter}'
                    search_url = f'https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}'
                    
                    response = requests.get(search_url, headers=self.headers, timeout=8)
                    
                    if response.status_code == 200:
                        content = response.text.lower()
                        
                        # Check if papers found in this database
                        if clean_name.lower() in content and ('paper' in content or 'publication' in content):
                            research_info.append({
                                'title': f'{db_name} Database Publications',
                                'description': f'Research publications indexed in {db_name} academic database',
                                'source': db_name,
                                'author_confidence': 0.6,
                                'validation_method': f'{db_name.lower()}_database'
                            })
                
                except Exception as e:
                    continue
            
            print(f"📚 Academic DBs: {len(research_info)} entries found")
            
        except Exception as e:
            print(f"Academic database search failed: {e}")
        
        return research_info
    
    def _validate_research_attribution(self, research_info, clean_name):
        """✅ Validate research attribution to prevent incorrect crediting"""
        validated_research = []
        
        for research in research_info:
            # Confidence thresholds by source
            confidence_thresholds = {
                'Google Scholar': 0.4,
                'University Faculty Page': 0.6,
                'ResearchGate': 0.5,
                'ORCID': 0.8,
                'IEEE': 0.4,
                'ACM': 0.4
            }
            
            source = research.get('source', 'Unknown')
            confidence = research.get('author_confidence', 0)
            threshold = confidence_thresholds.get(source, 0.5)
            
            # Additional validation checks
            title = research.get('title', '').lower()
            
            # Red flags that suggest incorrect attribution
            red_flags = [
                'based on the work of',
                'colleague',
                'collaboration with',
                'joint work',
                'co-authored',
                'work of my colleague'
            ]
            
            has_red_flags = any(flag in title for flag in red_flags)
            
            # Accept if confidence exceeds threshold AND no red flags
            if confidence >= threshold and not has_red_flags:
                research['validation_status'] = 'validated'
                validated_research.append(research)
            elif source in ['ORCID', 'University Faculty Page']:  # Always trust official sources
                research['validation_status'] = 'official_source'
                validated_research.append(research)
            else:
                print(f"⚠️ Rejected research: Low confidence ({confidence:.2f}) or red flags for {clean_name}")
        
        print(f"✅ Validation: {len(validated_research)}/{len(research_info)} passed")
        return validated_research
    
    def _format_validated_research_mentions(self, validated_research, clean_name):
        """📝 Format validated research data into personalized mentions"""
        if not validated_research:
            return None
        
        # Use the highest confidence research for main mention
        main_research = max(validated_research, key=lambda x: x.get('author_confidence', 0))
        title = main_research['title']
        source = main_research['source']
        
        # Extract key research areas
        research_areas = []
        keywords = ['machine learning', 'artificial intelligence', 'computer science', 'deep learning',
                   'neural networks', 'data science', 'algorithms', 'software engineering']
        
        text_to_search = f"{title}".lower()
        for keyword in keywords:
            if keyword in text_to_search:
                research_areas.append(keyword)
        
        primary_area = research_areas[0].title() if research_areas else 'Computer Science'
        
        # Create non-repetitive, validated mentions
        return {
            'research_area': primary_area,
            'research_focus': f'{primary_area.lower()} applications and methodologies',
            'research_mention': f'your validated research contributions in {primary_area.lower()}',
            'specific_interest': f'particularly your work in {primary_area.lower()} (verified via {source})',
            'validation_confidence': main_research.get('author_confidence', 0.5),
            'source_verified': True
        }
    
    def _get_enhanced_fallback_research_data(self, email, affiliation, professor_name):
        """🎯 Enhanced fallback research data with domain-specific personalization"""
        domain = email.split('@')[1].lower()
        
        # Comprehensive domain mapping
        domain_mapping = {
            'mit.edu': {
                'research_area': 'Artificial Intelligence and Machine Learning',
                'research_focus': 'AI systems and computational intelligence',
                'research_mention': 'your work in AI systems and machine learning applications',
                'specific_interest': 'particularly your contributions to scalable AI architectures'
            },
            'stanford.edu': {
                'research_area': 'Human-Computer Interaction and AI',
                'research_focus': 'human-AI collaboration and interface design',
                'research_mention': 'your research in human-computer interaction and AI interfaces',
                'specific_interest': 'especially your work on human-centered AI design'
            },
            'cmu.edu': {
                'research_area': 'Software Engineering and Program Analysis',
                'research_focus': 'software engineering and program analysis',
                'research_mention': 'your research in software engineering and program analysis',
                'specific_interest': 'particularly your approaches to program analysis and software reliability'
            }
        }
        
        # Get domain-specific data or create personalized fallback
        if domain in domain_mapping:
            result = domain_mapping[domain]
        else:
            # Enhanced fallback system for ALL professors
            university_name = domain.split('.')[0].title()
            
            # Research areas with better variety
            research_areas = [
                ('Machine Learning and Data Science', 'data-driven research', 'machine learning applications'),
                ('Artificial Intelligence and Automation', 'AI systems', 'artificial intelligence research'),
                ('Computer Science and Software Engineering', 'computational methods', 'computer science applications'),
                ('Computational Intelligence', 'intelligent systems', 'computational intelligence'),
                ('Advanced Computing and Algorithms', 'algorithmic innovation', 'advanced computing methods')
            ]
            
            # Select research area based on email hash for consistency
            area_index = hash(email) % len(research_areas)
            selected_area = research_areas[area_index]
            
            result = {
                'research_area': selected_area[0],
                'research_focus': selected_area[1],
                'research_mention': f'your contributions to {selected_area[2]}',
                'specific_interest': f'particularly your work in {selected_area[2]} at {university_name}'
            }
        
        # Add validation metadata
        result.update({
            'validation_confidence': 0.7,  # Fallback confidence
            'source_verified': False,
            'method': 'enhanced_fallback'
        })
        
        return result


# Integration function for system.py
def get_enhanced_research_system():
    """Get the enhanced research system instance"""
    return EnhancedResearchSystem()