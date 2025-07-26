# InternMailer: AI-Powered Academic Outreach Platform

## 🎯 Project Overview

**InternMailer** is an intelligent, automated system designed to help students secure research internships by streamlining the academic outreach process. It combines AI-powered resume parsing, semantic matching, and automated email workflows to create personalized outreach campaigns to professors worldwide.

## 🏗️ Architecture & Components

### Core Modules

#### 1. **Resume Parser** (`resume_parser.py`)
- **Purpose**: Extracts skills, projects, courses, and experience from PDF resumes
- **Technology**: PyMuPDF + Ollama LLM (Gemma3)
- **Features**:
  - PDF text extraction
  - LLM-powered structured data extraction
  - Fallback to basic text extraction if LLM fails
  - JSON output for downstream processing

#### 2. **Professor Scraper** (`professor_scraper.py`)
- **Purpose**: Collects professor data from CSRankings and personal homepages
- **Data Sources**: CSRankings CSV files, professor homepages
- **Features**:
  - CSV parsing for basic professor info
  - Web scraping for research areas and contact details
  - Email validation and verification

#### 3. **Semantic Matcher** (`semantic_matcher.py`)
- **Purpose**: Matches student profiles with professor research areas
- **Technology**: Sentence Transformers (all-MiniLM-L6-v2)
- **Features**:
  - Embedding-based similarity matching
  - Configurable similarity thresholds
  - Research area and homepage content analysis

#### 4. **Email Generator** (`email_generator.py`)
- **Purpose**: Creates personalized outreach emails
- **Technology**: Ollama LLM + Jinja2 templates
- **Features**:
  - LLM-powered personalized email generation
  - Template fallback system
  - Professional and informal tone options
  - Custom prompt support

#### 5. **Gmail Sender** (`gmail_sender.py`)
- **Purpose**: Sends emails with attachments and tracks delivery
- **Features**:
  - SMTP authentication with Gmail
  - Resume attachment support
  - Email validation before sending
  - Delivery status logging
  - Rate limiting and error handling

#### 6. **Follow-up Scheduler** (`followup_scheduler.py`)
- **Purpose**: Manages follow-up email campaigns
- **Features**:
  - SQLite database for tracking
  - Automated follow-up scheduling
  - Response tracking
  - Campaign analytics

### Frontend Interface
- **Technology**: Streamlit
- **Features**:
  - Resume upload and parsing
  - Campaign configuration
  - Real-time progress tracking
  - Analytics dashboard
  - Email preview functionality

## 📊 Current Status & Metrics

### Email Campaign Performance
- **Total Emails Sent**: 119 (as of latest campaign)
- **Target Universities**: MIT, Imperial College London, and others
- **Success Rate**: High delivery rate, some bounce-backs from invalid addresses
- **Campaign Duration**: Multiple campaigns from July 24-26, 2025

### Data Sources
- **Professor Database**: 375+ professors from CSRankings
- **Universities Covered**: Top-ranked institutions worldwide
- **Research Areas**: AI, ML, Computer Science, Data Science

## 🚨 Issues Identified & Fixed

### 1. **Email Generation Issues** ✅ FIXED
- **Problem**: Empty placeholders in emails ("your research on .")
- **Root Cause**: Field mapping mismatch between CSV columns and template variables
- **Solution**: Enhanced field mapping with fallback values

### 2. **LLM Integration Issues** ✅ FIXED
- **Problem**: `custom_prompt` parameter not accepted by `generate_with_llm()`
- **Root Cause**: Missing parameter in method signature
- **Solution**: Added `custom_prompt` parameter with proper handling

### 3. **Email Validation Issues** ✅ FIXED
- **Problem**: Invalid emails like `lvilanov@doc.ic.ac.uk` being sent
- **Root Cause**: Insufficient validation checking only `email_valid` field
- **Solution**: Enhanced validation including format, TLD, and validation status

### 4. **Scraper Initialization Issues** ✅ FIXED
- **Problem**: `scraper` object referenced without initialization
- **Root Cause**: Missing scraper instantiation
- **Solution**: Added proper initialization with error handling

## 🎯 Project Definition & Scope

### Primary Goals
1. **Automate Academic Outreach**: Reduce manual effort in finding and contacting professors
2. **Improve Match Quality**: Use AI to match students with relevant research areas
3. **Scale Outreach**: Enable sending hundreds of personalized emails efficiently
4. **Track Success**: Monitor response rates and campaign effectiveness

### Target Users
- **Primary**: Undergraduate and graduate students seeking research internships
- **Secondary**: Academic advisors, career counselors
- **Tertiary**: Research institutions looking to attract talent

### Success Metrics
- **Email Delivery Rate**: >95%
- **Response Rate**: >5% (industry standard for cold outreach)
- **Match Quality**: Semantic similarity scores >0.3
- **Campaign Efficiency**: <5 minutes setup time

## 🔧 Technical Stack

### Backend
- **Language**: Python 3.8+
- **AI/ML**: Ollama (Gemma3), Sentence Transformers
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Web Scraping**: BeautifulSoup4, Requests
- **PDF Processing**: PyMuPDF, pdfminer.six

### Frontend
- **Framework**: Streamlit
- **UI Components**: File upload, progress bars, data tables
- **Real-time Updates**: WebSocket-like updates via Streamlit

### Infrastructure
- **Email**: Gmail SMTP with app passwords
- **Database**: SQLite for follow-up tracking
- **File Storage**: Local file system
- **LLM**: Local Ollama server

## 🚀 Future Enhancements

### Short-term (1-2 months)
1. **Enhanced Email Validation**: MX record checking
2. **Rate Limiting**: Prevent Gmail API limits
3. **Retry Logic**: Automatic retry for failed emails
4. **Better Analytics**: Response tracking and reporting

### Medium-term (3-6 months)
1. **Multi-language Support**: International outreach
2. **Advanced Matching**: Multi-modal matching (skills + research)
3. **Template Library**: Multiple email templates
4. **A/B Testing**: Email subject and content optimization

### Long-term (6+ months)
1. **Web Application**: Replace Streamlit with React/Next.js
2. **Cloud Deployment**: AWS/Azure hosting
3. **API Integration**: LinkedIn, ResearchGate APIs
4. **Machine Learning Pipeline**: Continuous model improvement

## 📈 Business Model Potential

### Revenue Streams
1. **Freemium Model**: Basic features free, premium features paid
2. **Institutional Licenses**: University-wide deployments
3. **Consulting Services**: Custom implementations
4. **Data Services**: Anonymized analytics and insights

### Market Size
- **Target Market**: 20M+ students globally seeking research opportunities
- **Addressable Market**: $500M+ in career services and academic outreach
- **Competitive Advantage**: AI-powered personalization and automation

## 🛠️ Development Roadmap

### Phase 1: Core Stability (Current)
- ✅ Fix email generation issues
- ✅ Improve validation and error handling
- ✅ Enhance logging and monitoring
- 🔄 Add comprehensive testing

### Phase 2: Feature Enhancement
- 📋 Advanced email templates
- 📋 Better professor data sources
- 📋 Improved matching algorithms
- 📋 Enhanced analytics dashboard

### Phase 3: Scale & Monetization
- 📋 Web application development
- 📋 Cloud infrastructure
- 📋 API development
- 📋 Partnership integrations

## 💡 Key Insights & Recommendations

### Technical Recommendations
1. **Implement comprehensive testing**: Unit tests for all modules
2. **Add monitoring**: Real-time error tracking and alerting
3. **Optimize performance**: Caching and parallel processing
4. **Enhance security**: API key management and data encryption

### Business Recommendations
1. **Focus on user experience**: Simplify the onboarding process
2. **Build community**: User feedback and feature requests
3. **Partnership strategy**: University career services integration
4. **Data-driven decisions**: Analytics to guide feature development

### Marketing Recommendations
1. **Content marketing**: Blog posts about academic outreach
2. **Social proof**: Success stories and testimonials
3. **Educational content**: Webinars and tutorials
4. **Community building**: Student and academic communities

This project has significant potential to revolutionize how students approach academic outreach, making it more efficient, personalized, and successful. 