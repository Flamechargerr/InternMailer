# Debug AI providers and show why they failed
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import requests
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("AI PROVIDER DEBUG")
print("=" * 60)

# Test Ollama
print("\n1. OLLAMA:")
try:
    r = requests.get("http://localhost:11434/api/version", timeout=5)
    if r.status_code == 200:
        print(f"   STATUS: RUNNING - {r.json()}")
    else:
        print(f"   STATUS: ERROR - {r.status_code}")
except Exception as e:
    print(f"   STATUS: NOT RUNNING - {e}")

# Test Gemini
print("\n2. GEMINI:")
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print(f"   API KEY: Found ({gemini_key[:10]}...)")
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'OK' if working")
        print(f"   STATUS: WORKING - Response: {response.text[:50]}")
    except Exception as e:
        print(f"   STATUS: ERROR - {e}")
else:
    print("   API KEY: NOT FOUND")

# Test Groq
print("\n3. GROQ:")
groq_key = os.getenv('GROQ_API_KEY')
if groq_key:
    print(f"   API KEY: Found ({groq_key[:10]}...)")
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": "Say OK if working"}],
                "max_tokens": 10
            },
            timeout=10
        )
        if r.status_code == 200:
            print(f"   STATUS: WORKING - {r.json()['choices'][0]['message']['content']}")
        else:
            print(f"   STATUS: ERROR - {r.status_code} - {r.text[:100]}")
    except Exception as e:
        print(f"   STATUS: ERROR - {e}")
else:
    print("   API KEY: NOT FOUND")

print("\n" + "=" * 60)
