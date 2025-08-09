# Integration To-Do Checklist for app.py Creation

## ✅ COMPLETED
- [x] Fresh virtual environment created and activated
- [x] All dependencies from requirements.txt installed successfully
- [x] Pytest runs with 100% success rate (1/1 tests passing)
- [x] All Streamlit pages compile without syntax errors
- [x] Core module imports verified (src/ directory modules working)

## ❌ CRITICAL ISSUES TO FIX

### 1. Missing Module Implementation
**Priority: HIGH**
- [ ] **Create `send_email_with_cv` function**: Currently missing from pages/01_Professor_Outreach.py
  - **Location**: Line 85 in pages/01_Professor_Outreach.py
  - **Solution**: Create this function in src/email_sender.py or create a new module
  - **Function signature needed**: `send_email_with_cv(professor_data, recipient_email)`

### 2. Missing/Incorrect Imports  
**Priority: HIGH**
- [ ] **Fix missing imports in pages/02_Job_Applications.py**:
  - `from hr_email_generator import HREmailGenerator` ✅ (file exists)
  - `from job_parser import JobParser` ✅ (file exists) 
  - `from cv_customizer import CVCustomizer` ✅ (file exists)
  - `from application_tracker import ApplicationTracker` ✅ (file exists)
  - `from hr_finder import HRFinder` ✅ (file exists)

### 3. Environment Variables Configuration
**Priority: HIGH** 
- [ ] **Update .env file with required variables**:
  ```env
  # Currently missing from .env:
  GMAIL_USER=your-email@gmail.com
  GMAIL_APP_PASSWORD=your-app-password
  AZURE_OPENAI_API_KEY=your-azure-key
  AZURE_OPENAI_ENDPOINT=your-azure-endpoint
  ```

### 4. Hard-coded Paths Issues
**Priority: MEDIUM**
- [ ] **Fix hard-coded paths in pages/03_Professor_Scraper.py**:
  - Line 177: `"data/scraped_professors.csv"` - should use dynamic path
- [ ] **Fix hard-coded paths in pages/02_Job_Applications.py**:
  - Lines 72, 76, 82-84: Various "data/" references should be dynamic
  - Lines 177-178, 193, 221, 227, 239, 263: Hard-coded data directory paths

### 5. Missing Data Files
**Priority: MEDIUM**
- [ ] **Ensure required data files exist**:
  - `data/base_cv.json` (required by CVCustomizer)
  - `companies.json` (referenced in Job Applications page)
  - Professor CSV files in data/ directory (for Professor Scraper)

## 🔧 SUGGESTED IMPROVEMENTS

### 6. Configuration Management
**Priority: MEDIUM**
- [ ] **Implement centralized path management**: 
  - Use `src/shared/config_manager.py` for all path references
  - Replace all hard-coded "data/" paths with config manager calls

### 7. Missing Assets Check
**Priority: LOW**
- [ ] **Verify template files**: Check if email templates exist in templates/ directory
- [ ] **Verify resume directory**: Ensure resumes/ directory exists and is writable

### 8. Error Handling Improvements
**Priority: LOW**
- [ ] **Add graceful fallbacks** for missing files in all pages
- [ ] **Improve error messages** for missing environment variables

## 📋 INTEGRATION TESTING PLAN

### Before Creating app.py:
1. [ ] **Test individual pages in isolation**:
   ```bash
   streamlit run pages/01_Professor_Outreach.py
   streamlit run pages/02_Job_Applications.py  
   streamlit run pages/03_Professor_Scraper.py
   ```

2. [ ] **Verify all imports work**:
   ```bash
   python test_imports.py
   ```

3. [ ] **Test with minimal data**:
   - Create sample data files in data/ directory
   - Test basic functionality of each page

### After Creating app.py:
1. [ ] **Integration testing**: Verify all pages work together
2. [ ] **Navigation testing**: Ensure page navigation works properly
3. [ ] **Configuration testing**: Verify environment variables are loaded correctly

## 🚀 READY FOR app.py CREATION?

**Current Status**: ❌ NOT READY

**Blocking Issues**:
1. Missing `send_email_with_cv` function
2. Missing environment variables in .env file
3. Hard-coded paths need fixing

**To become ready**:
1. Fix the 3 blocking issues above
2. Test all pages individually  
3. Verify all imports work correctly

## 📁 RECOMMENDED FILE STRUCTURE FOR app.py

```
app.py (main entry point)
├── pages/
│   ├── 01_Professor_Outreach.py
│   ├── 02_Job_Applications.py  
│   └── 03_Professor_Scraper.py
├── src/
│   ├── shared/
│   │   ├── config_manager.py
│   │   └── ui_components.py
│   └── [other modules]
├── data/
│   ├── base_cv.json
│   └── [CSV files]
├── resumes/
├── templates/
└── .env
```

## 🔍 TESTING COMMANDS

```bash
# Test environment setup
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('GMAIL_USER:', os.getenv('GMAIL_USER', 'NOT SET'))"

# Test imports
python test_imports.py

# Test individual pages (after fixing issues)
streamlit run pages/01_Professor_Outreach.py --server.headless true
streamlit run pages/02_Job_Applications.py --server.headless true  
streamlit run pages/03_Professor_Scraper.py --server.headless true

# Test full integration (after creating app.py)
streamlit run app.py
```

---
**Generated**: 2025-08-05
**Status**: Audit Complete - Ready for Fixes
