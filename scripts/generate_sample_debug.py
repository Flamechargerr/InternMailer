# Direct file output with debug log
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Redirect stdout to capture debug output
import io
debug_output = io.StringIO()
old_stdout = sys.stdout

from ai_research_validator import get_research_validator
from system import VerifiedEmailSystem

# Capture the AI debug output
sys.stdout = debug_output
validator = get_research_validator()
vs = VerifiedEmailSystem()

contacts = vs.get_verified_contacts(max_contacts=5)
prof = random.choice(contacts)
name, email, affiliation, conf, grade = prof

result = validator.generate_validated_email(name, email, affiliation)
sys.stdout = old_stdout

debug_log = debug_output.getvalue()

output = f"""
================================================================================
RANDOM PROFESSOR EMAIL PREVIEW
================================================================================

PROFESSOR INFO:
  Name: {name}
  Email: {email}
  University: {affiliation}
  Grade: {grade} | Confidence: {conf}%

DEBUG LOG:
{debug_log}

VALIDATION:
  Status: {result.get('validation_status', 'UNKNOWN')}
  Research Area: {result.get('research_area', 'Unknown')}
  Papers Found: {result.get('papers_found', 0)}
  Confidence: {result.get('confidence', 0):.0%}

================================================================================
SUBJECT LINE:
================================================================================
{result.get('subject', 'No subject')}

================================================================================
EMAIL BODY:
================================================================================
{result.get('body', 'No body generated')}
================================================================================
"""

with open('email_sample_debug.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print("Done - check email_sample_debug.txt")
