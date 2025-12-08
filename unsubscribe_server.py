"""
InternMailer - Unsubscribe Server
CAN-SPAM Act Compliant Unsubscribe Handler
"""

from flask import Flask, request, render_template_string
import sqlite3
from datetime import datetime
import hashlib
import hmac
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
SECRET_KEY = os.getenv('UNSUBSCRIBE_SECRET_KEY', 'your-secret-key-change-this')

def create_unsubscribe_token(email):
    """Create secure token for email address"""
    timestamp = str(int(datetime.now().timestamp()))
    message = f"{email}:{timestamp}"
    signature = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    token = base64.urlsafe_b64encode(f"{message}:{signature}".encode()).decode()
    return token

def verify_unsubscribe_token(token):
    """Verify and decode token to extract email"""
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.split(':')
        if len(parts) != 3:
            return None
        
        email, timestamp, signature = parts
        message = f"{email}:{timestamp}"
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected_signature):
            return email
        return None
    except Exception:
        return None

def add_to_unsubscribe_list(email, reason='User request'):
    """Add email to unsubscribe database"""
    db_path = 'campaign_results/advanced_tracking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO unsubscribes (email, unsubscribe_date, reason)
            VALUES (?, ?, ?)
        ''', (email, datetime.now().isoformat(), reason))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding to unsubscribe list: {e}")
        return False
    finally:
        conn.close()

# HTML Templates
UNSUBSCRIBE_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Unsubscribe - InternMailer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .email {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            margin: 20px 0;
        }
        button {
            background: #dc3545;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 20px;
        }
        button:hover {
            background: #c82333;
        }
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Unsubscribe from InternMailer</h1>
        <p>You are about to unsubscribe the following email address:</p>
        <div class="email">{{ email }}</div>
        <p>You will no longer receive emails from us. This action is permanent.</p>
        <form method="POST">
            <button type="submit">Confirm Unsubscribe</button>
        </form>
    </div>
</body>
</html>
'''

SUCCESS_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Unsubscribed - InternMailer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #28a745;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #c3e6cb;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>✓ Successfully Unsubscribed</h1>
        <div class="success">
            <strong>{{ email }}</strong> has been removed from our mailing list.
        </div>
        <p>You will no longer receive emails from InternMailer.</p>
        <p>If you unsubscribed by mistake, please contact us at tripathy.anamay23@gmail.com</p>
    </div>
</body>
</html>
'''

ERROR_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Error - InternMailer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #dc3545;
            margin-bottom: 20px;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Invalid Unsubscribe Link</h1>
        <div class="error">
            {{ error_message }}
        </div>
    </div>
</body>
</html>
'''

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    token = request.args.get('token', '')
    
    if not token:
        return render_template_string(ERROR_PAGE, 
            error_message="Missing unsubscribe token. Please use the link provided in your email.")
    
    email = verify_unsubscribe_token(token)
    
    if not email:
        return render_template_string(ERROR_PAGE,
            error_message="Invalid or expired unsubscribe link. Please contact support if this problem persists.")
    
    if request.method == 'POST':
        # Process unsubscribe
        if add_to_unsubscribe_list(email):
            return render_template_string(SUCCESS_PAGE, email=email)
        else:
            return render_template_string(ERROR_PAGE,
                error_message="An error occurred while processing your request. Please try again.")
    
    # Show confirmation form
    return render_template_string(UNSUBSCRIBE_FORM, email=email)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'unsubscribe-server'}

if __name__ == '__main__':
    print("🚀 Starting Unsubscribe Server on http://localhost:5000")
    print("📧 Unsubscribe endpoint: http://localhost:5000/unsubscribe?token=...")
    app.run(host='0.0.0.0', port=5000, debug=False)
