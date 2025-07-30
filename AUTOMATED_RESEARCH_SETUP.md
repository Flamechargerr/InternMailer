# 🔬 Automated Professor Research System

## Quick Setup & Usage

### 1. Install Dependencies
```bash
pip install requests
```

### 2. Add Your Target Professors
Edit `data/professors.json` with your professor list:
```json
[
  {
    "name": "Prof. Sarah Chen",
    "university": "Stanford University", 
    "email": "schen@cs.stanford.edu",
    "department": "Computer Science"
  },
  {
    "name": "Prof. Michael Rodriguez",
    "university": "MIT",
    "email": "mrodriguez@csail.mit.edu", 
    "department": "CSAIL"
  }
]
```

### 3. Run the Automation
```bash
python run_research_automation.py
```

## What It Does Automatically

### 🔍 **Research Phase:**
- Fetches recent publications via Semantic Scholar API
- Analyzes research evolution and trends
- Identifies research areas and methodologies
- Finds personalization connections with your background

### 📊 **Quality Scoring:**
- Rates each professor (1-10 scale) based on:
  - Number of recent publications
  - Citation counts
  - Alignment with your interests
  - Personalization potential

### ✉️ **Email Generation:**
- Creates personalized emails for high-quality matches (score ≥7)
- Includes specific paper references
- Mentions relevant connections to your work
- Avoids generic language

### 📁 **Output Files:**
- `data/research_results_TIMESTAMP.json` - Complete research data
- `logs/research_automation.log` - Process logs

## Sample Output

```
🔍 Starting automated research...
✅ Prof. Sarah Chen (Stanford University) - Quality Score: 8
   Research Areas: Machine Learning, AI Ethics, Human-Computer Interaction
✅ Prof. Michael Rodriguez (MIT) - Quality Score: 7  
   Research Areas: Robotics, Computer Vision, Autonomous Systems

Research completed! Generated 2 personalized emails.
```

## Customization Options

### Adjust Quality Threshold
Edit `src/automated_research_system.py`:
```python
"min_quality_score": 7,  # Only generate emails for scores ≥7
```

### Modify Your Profile
Update the `load_user_profile()` function with your specific:
- Experience and projects
- Technical skills
- Research interests
- Unique perspectives

### Batch Size
Control how many professors to process:
```python
"max_professors_per_batch": 10,
```

## Advanced Features

### 1. **Web Scraping Integration**
The system includes placeholders for faculty page scraping. You can integrate with:
- BeautifulSoup for HTML parsing
- Selenium for dynamic content
- University-specific APIs

### 2. **Enhanced Personalization**
The system automatically:
- Matches your keywords with professor research
- Identifies unique value propositions
- Generates specific email hooks
- Avoids outdated research areas

### 3. **Rate Limiting**
Built-in delays prevent API abuse:
- 2-second delays between professors
- Configurable timeouts
- Error handling and logging

## Integration with Existing System

This automated research system integrates with your existing `internmailing` setup:

- Uses the same `data/` directory structure
- Compatible with your email sending system
- Maintains quality scoring for follow-up decisions
- Logs all activities for monitoring

## Quality Metrics

The system only generates emails for professors with:
- **Recent publications** (last 3 years)
- **Strong personalization potential** (≥3 connection points)
- **High research alignment** with your background
- **Active research presence** (citations, ongoing work)

This ensures you only send emails to professors where you have a genuine research fit and strong personalization potential.

## Next Steps

1. **Add your professors** to `data/professors.json`
2. **Run the automation**: `python run_research_automation.py`
3. **Review generated emails** in the results file
4. **Send high-quality matches** using your existing email system
5. **Monitor responses** and adjust quality thresholds

The goal is to transform your outreach from quantity-based to quality-based, ensuring every email you send is deeply personalized and research-backed.
