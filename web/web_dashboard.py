#!/usr/bin/env python3
"""
🌐 InternMailer Web Dashboard
=============================
Visual web interface for managing all InternMailer features:
- Send emails with visual progress
- Monitor inbox and replies
- Run ATS Optimizer
- View campaign statistics
- Control the automation daemon

Usage:
    python web_dashboard.py
    
Then open http://localhost:5000 in your browser
"""

import os
import sys
import json
import sqlite3
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for, send_file
from flask import session
from werkzeug.utils import secure_filename

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import InternMailer components
try:
    from core.email_system import EmailSystem
    from web.ats_optimizer import ATSOptimizer
    from core.unified_ai_provider import get_unified_ai_provider
    EMAIL_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Email system not available: {e}")
    EMAIL_SYSTEM_AVAILABLE = False

app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global state
daemon_process = None
campaign_stats = {
    'emails_sent': 0,
    'emails_failed': 0,
    'replies_received': 0,
    'last_updated': None
}

# ============== ROUTES ==============

@app.route('/')
def index():
    """Main dashboard page"""
    stats = get_campaign_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/stats')
def api_stats():
    """Get current campaign statistics"""
    return jsonify(get_campaign_stats())

@app.route('/send-emails', methods=['POST'])
def send_emails():
    """Send emails via API"""
    data = request.json
    count = data.get('count', 10)
    
    def send_task():
        try:
            system = EmailSystem()
            result = system.send_campaign(count=count)
            campaign_stats['emails_sent'] += result.get('sent', 0)
            campaign_stats['emails_failed'] += result.get('failed', 0)
            campaign_stats['last_updated'] = datetime.now().isoformat()
        except Exception as e:
            print(f"Error sending emails: {e}")
    
    # Run in background thread
    thread = threading.Thread(target=send_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'count': count})

@app.route('/preview-emails', methods=['GET'])
def preview_emails():
    """Get email previews"""
    count = request.args.get('count', 3, type=int)
    
    try:
        system = EmailSystem()
        previews = system.preview_emails(count=count)
        return jsonify({'status': 'success', 'previews': previews})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ats-optimizer', methods=['GET', 'POST'])
def ats_optimizer_page():
    """ATS Optimizer page"""
    if request.method == 'POST':
        job_description = request.form.get('job_description', '')
        company_name = request.form.get('company_name', 'Company')
        
        if not job_description:
            flash('Please enter a job description', 'error')
            return redirect(url_for('ats_optimizer_page'))
        
        try:
            optimizer = ATSOptimizer()
            result = optimizer.optimize_for_job(job_description)
            
            return render_template('ats_result.html', 
                                 result=result,
                                 company=company_name)
        except Exception as e:
            flash(f'Error optimizing: {str(e)}', 'error')
            return redirect(url_for('ats_optimizer_page'))
    
    return render_template('ats_optimizer.html')

@app.route('/contacts')
def contacts_page():
    """Contacts management page"""
    contacts = get_contacts()
    return render_template('contacts.html', contacts=contacts)

@app.route('/replies')
def replies_page():
    """Replies monitoring page"""
    replies = get_replies()
    return render_template('replies.html', replies=replies)

@app.route('/settings')
def settings_page():
    """Settings page"""
    config = get_current_config()
    return render_template('settings.html', config=config)

@app.route('/api/test-groq')
def test_groq():
    """Test Groq API connection"""
    try:
        from unified_ai_provider import get_unified_ai_provider
        provider = get_unified_ai_provider()
        
        # Try a simple test call
        groq_key = os.getenv('GROQ_API_KEY', '')
        if groq_key:
            return jsonify({
                'status': 'success',
                'message': 'Groq API key is configured',
                'key_preview': groq_key[:10] + '...'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Groq API key not found in environment'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/daemon/start', methods=['POST'])
def start_daemon():
    """Start the automation daemon"""
    global daemon_process
    
    if daemon_process and daemon_process.poll() is None:
        return jsonify({'status': 'error', 'message': 'Daemon already running'})
    
    try:
        daemon_process = subprocess.Popen(
            [sys.executable, 'daemon.py', '--start'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return jsonify({'status': 'success', 'message': 'Daemon started'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/daemon/stop', methods=['POST'])
def stop_daemon():
    """Stop the automation daemon"""
    global daemon_process
    
    if daemon_process:
        daemon_process.terminate()
        daemon_process = None
        return jsonify({'status': 'success', 'message': 'Daemon stopped'})
    
    return jsonify({'status': 'error', 'message': 'Daemon not running'})

@app.route('/api/daemon/status')
def daemon_status():
    """Get daemon status"""
    global daemon_process
    
    if daemon_process and daemon_process.poll() is None:
        return jsonify({'status': 'running'})
    else:
        return jsonify({'status': 'stopped'})

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download optimized files"""
    safe_filename = secure_filename(filename)
    file_path = Path('optimized_documents') / safe_filename
    
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

# ============== HELPER FUNCTIONS ==============

def get_campaign_stats():
    """Get campaign statistics from database"""
    stats = {
        'emails_sent': 0,
        'emails_failed': 0,
        'replies_received': 0,
        'followups_sent': 0,
        'contacts_total': 0,
        'contacts_contacted': 0,
        'last_updated': None
    }
    
    # Try to get from tracking database
    try:
        db_path = 'campaign_results/email_tracking.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count sent emails
            cursor.execute('SELECT COUNT(*) FROM sent_emails')
            stats['emails_sent'] = cursor.fetchone()[0]
            
            # Count unique contacts
            cursor.execute('SELECT COUNT(DISTINCT email) FROM sent_emails')
            stats['contacts_contacted'] = cursor.fetchone()[0]
            
            conn.close()
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    # Add in-memory stats
    stats['emails_sent'] += campaign_stats['emails_sent']
    stats['emails_failed'] += campaign_stats['emails_failed']
    stats['replies_received'] += campaign_stats['replies_received']
    
    return stats

def get_contacts():
    """Get contacts from database"""
    contacts = []
    
    try:
        db_path = 'data/verified_professors.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, email, affiliation, contacted 
                FROM verified_contacts 
                LIMIT 100
            ''')
            
            for row in cursor.fetchall():
                contacts.append({
                    'name': row[0],
                    'email': row[1],
                    'company': row[2],
                    'contacted': row[3] == 'yes'
                })
            
            conn.close()
    except Exception as e:
        print(f"Error getting contacts: {e}")
    
    return contacts

def get_replies():
    """Get replies from inbox monitor"""
    replies = []
    
    try:
        db_path = 'campaign_results/inbox_monitor.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sender, subject, received_date, category, sentiment
                FROM replies
                ORDER BY received_date DESC
                LIMIT 50
            ''')
            
            for row in cursor.fetchall():
                replies.append({
                    'sender': row[0],
                    'subject': row[1],
                    'date': row[2],
                    'category': row[3],
                    'sentiment': row[4]
                })
            
            conn.close()
    except Exception as e:
        print(f"Error getting replies: {e}")
    
    return replies

def get_current_config():
    """Get current configuration"""
    return {
        'gmail_user': os.getenv('GMAIL_USER', ''),
        'groq_key': os.getenv('GROQ_API_KEY', '')[:10] + '...' if os.getenv('GROQ_API_KEY') else '',
        'max_emails_per_day': os.getenv('MAX_EMAILS_PER_DAY', '100'),
        'followup_days': os.getenv('FOLLOWUP_DAYS', '7'),
    }

# ============== TEMPLATE CREATION ==============

def create_templates():
    """Create HTML templates for the dashboard"""
    # Get the correct templates directory relative to project root
    base_dir = Path(__file__).parent.parent
    templates_dir = base_dir / 'templates' / 'web'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Base template
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}InternMailer Dashboard{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .navbar h1 {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .nav-links {
            display: flex;
            gap: 1.5rem;
            margin-top: 1rem;
        }
        
        .nav-links a {
            color: rgba(255,255,255,0.9);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.3s;
        }
        
        .nav-links a:hover, .nav-links a.active {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .card h2 {
            margin-bottom: 1rem;
            color: #444;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
        }
        
        .stat-card h3 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .stat-card p {
            opacity: 0.9;
        }
        
        .btn {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #6c757d;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 1rem;
        }
        
        .form-group textarea {
            min-height: 150px;
            resize: vertical;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            font-weight: 600;
            color: #666;
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        
        .status-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <h1>🤖 InternMailer</h1>
        <div class="nav-links">
            <a href="{{ url_for('index') }}" class="{% if request.endpoint == 'index' %}active{% endif %}">Dashboard</a>
            <a href="{{ url_for('ats_optimizer_page') }}" class="{% if request.endpoint == 'ats_optimizer_page' %}active{% endif %}">🎯 ATS Optimizer</a>
            <a href="{{ url_for('contacts_page') }}" class="{% if request.endpoint == 'contacts_page' %}active{% endif %}">📇 Contacts</a>
            <a href="{{ url_for('replies_page') }}" class="{% if request.endpoint == 'replies_page' %}active{% endif %}">📬 Replies</a>
            <a href="{{ url_for('settings_page') }}" class="{% if request.endpoint == 'settings_page' %}active{% endif %}">⚙️ Settings</a>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    {% block extra_js %}{% endblock %}
</body>
</html>'''
    
    (templates_dir / 'base.html').write_text(base_template)
    
    # Dashboard template
    dashboard_template = '''{% extends "base.html" %}

{% block title %}Dashboard - InternMailer{% endblock %}

{% block content %}
<div class="stats-grid">
    <div class="stat-card">
        <h3>{{ stats.emails_sent }}</h3>
        <p>Emails Sent</p>
    </div>
    <div class="stat-card">
        <h3>{{ stats.replies_received }}</h3>
        <p>Replies Received</p>
    </div>
    <div class="stat-card">
        <h3>{{ stats.contacts_contacted }}</h3>
        <p>Contacts Reached</p>
    </div>
    <div class="stat-card">
        <h3>{{ stats.followups_sent }}</h3>
        <p>Follow-ups Sent</p>
    </div>
</div>

<div class="card">
    <h2>📧 Quick Actions</h2>
    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
        <button class="btn" onclick="sendEmails()">Send 10 Emails</button>
        <button class="btn btn-secondary" onclick="previewEmails()">Preview Emails</button>
        <button class="btn btn-success" onclick="startDaemon()">Start Daemon</button>
        <button class="btn btn-danger" onclick="stopDaemon()">Stop Daemon</button>
    </div>
    <div id="status-message" style="margin-top: 1rem;"></div>
</div>

<div class="card">
    <h2>🎯 ATS Optimizer</h2>
    <p>Customize your resume and cover letter for specific job applications to maximize ATS scores.</p>
    <a href="{{ url_for('ats_optimizer_page') }}" class="btn" style="margin-top: 1rem;">Open ATS Optimizer</a>
</div>

<div class="card">
    <h2>📊 System Status</h2>
    <table>
        <tr>
            <td>Email System</td>
            <td><span class="status-badge status-success">✅ Available</span></td>
        </tr>
        <tr>
            <td>AI Provider (Groq)</td>
            <td><span class="status-badge status-success" id="groq-status">Checking...</span></td>
        </tr>
        <tr>
            <td>Automation Daemon</td>
            <td><span class="status-badge status-warning" id="daemon-status">Checking...</span></td>
        </tr>
    </table>
</div>
{% endblock %}

{% block extra_js %}
<script>
function sendEmails() {
    fetch('/send-emails', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({count: 10})
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('status-message').innerHTML = 
            '<div class="alert alert-success">✅ ' + data.status + ': Sending ' + data.count + ' emails</div>';
    })
    .catch(e => {
        document.getElementById('status-message').innerHTML = 
            '<div class="alert alert-error">❌ Error: ' + e.message + '</div>';
    });
}

function previewEmails() {
    fetch('/preview-emails?count=3')
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            let html = '<h3>Email Previews:</h3>';
            data.previews.forEach((preview, i) => {
                html += `<div style="margin: 1rem 0; padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                    <strong>Email ${i+1}:</strong><br>
                    <pre style="margin-top: 0.5rem; white-space: pre-wrap;">${preview}</pre>
                </div>`;
            });
            document.getElementById('status-message').innerHTML = html;
        }
    });
}

function startDaemon() {
    fetch('/api/daemon/start', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
        document.getElementById('status-message').innerHTML = 
            '<div class="alert alert-success">✅ ' + data.message + '</div>';
        updateDaemonStatus();
    });
}

function stopDaemon() {
    fetch('/api/daemon/stop', {method: 'POST'})
    .then(r => r.json())
    .then(data => {
        document.getElementById('status-message').innerHTML = 
            '<div class="alert alert-success">✅ ' + data.message + '</div>';
        updateDaemonStatus();
    });
}

function updateDaemonStatus() {
    fetch('/api/daemon/status')
    .then(r => r.json())
    .then(data => {
        const badge = document.getElementById('daemon-status');
        if (data.status === 'running') {
            badge.className = 'status-badge status-success';
            badge.textContent = '✅ Running';
        } else {
            badge.className = 'status-badge status-warning';
            badge.textContent = '⏹️ Stopped';
        }
    });
}

function checkGroq() {
    fetch('/api/test-groq')
    .then(r => r.json())
    .then(data => {
        const badge = document.getElementById('groq-status');
        if (data.status === 'success') {
            badge.className = 'status-badge status-success';
            badge.textContent = '✅ ' + data.message;
        } else {
            badge.className = 'status-badge status-error';
            badge.textContent = '❌ ' + data.message;
        }
    });
}

// Update status on page load
checkGroq();
updateDaemonStatus();
setInterval(updateDaemonStatus, 5000);
</script>
{% endblock %}'''
    
    (templates_dir / 'dashboard.html').write_text(dashboard_template)
    
    # ATS Optimizer template
    ats_template = '''{% extends "base.html" %}

{% block title %}ATS Optimizer - InternMailer{% endblock %}

{% block content %}
<div class="card">
    <h2>🎯 ATS Optimizer</h2>
    <p>Paste a job description below to automatically customize your resume and cover letter for maximum ATS compatibility.</p>
</div>

<div class="card">
    <form method="POST">
        <div class="form-group">
            <label for="company_name">Company Name (optional)</label>
            <input type="text" id="company_name" name="company_name" placeholder="e.g., Google">
        </div>
        
        <div class="form-group">
            <label for="job_description">Job Description *</label>
            <textarea id="job_description" name="job_description" 
                placeholder="Paste the full job description here..."></textarea>
        </div>
        
        <button type="submit" class="btn">🚀 Optimize Resume & Cover Letter</button>
    </form>
</div>

<div class="card">
    <h3>How it works:</h3>
    <ol style="margin-left: 1.5rem; line-height: 2;">
        <li>AI extracts keywords from the job description</li>
        <li>Your resume is customized with relevant keywords</li>
        <li>A tailored cover letter is generated</li>
        <li>ATS compatibility score is calculated (before/after)</li>
        <li>Download optimized PDFs ready to submit</li>
    </ol>
</div>
{% endblock %}'''
    
    (templates_dir / 'ats_optimizer.html').write_text(ats_template)
    
    # ATS Result template
    ats_result_template = '''{% extends "base.html" %}

{% block title %}ATS Results - InternMailer{% endblock %}

{% block content %}
<div class="card">
    <h2>✅ Optimization Complete</h2>
    <p>Your resume and cover letter have been optimized for <strong>{{ result.company_name }}</strong></p>
</div>

<div class="stats-grid">
    <div class="stat-card">
        <h3>{{ result.ats_score_before }}</h3>
        <p>ATS Score Before</p>
    </div>
    <div class="stat-card">
        <h3>{{ result.ats_score_after }}</h3>
        <p>ATS Score After</p>
    </div>
    <div class="stat-card">
        <h3>+{{ result.ats_score_after - result.ats_score_before }}</h3>
        <p>Points Improved</p>
    </div>
    <div class="stat-card">
        <h3>{{ result.keywords_found|length }}</h3>
        <p>Keywords Found</p>
    </div>
</div>

<div class="card">
    <h2>📥 Download Files</h2>
    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
        <a href="{{ url_for('download_file', filename=result.resume_path.split('/')[-1]) }}" class="btn">📄 Download Resume (.tex)</a>
        <a href="{{ url_for('download_file', filename=result.cover_letter_path.split('/')[-1]) }}" class="btn">📄 Download Cover Letter (.tex)</a>
        {% if result.pdf_resume_path %}
        <a href="{{ url_for('download_file', filename=result.pdf_resume_path.split('/')[-1]) }}" class="btn btn-success">📕 Resume PDF</a>
        {% endif %}
        {% if result.pdf_cover_letter_path %}
        <a href="{{ url_for('download_file', filename=result.pdf_cover_letter_path.split('/')[-1]) }}" class="btn btn-success">📕 Cover Letter PDF</a>
        {% endif %}
    </div>
</div>

<div class="card">
    <h2>🔑 Keywords Identified</h2>
    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        {% for keyword in result.keywords_found %}
        <span style="background: #e9ecef; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem;">{{ keyword }}</span>
        {% endfor %}
    </div>
</div>

<div class="card">
    <h2>📊 Optimization Report</h2>
    <p>A detailed report has been saved to <code>optimized_documents/optimization_report.md</code></p>
    <a href="{{ url_for('ats_optimizer_page') }}" class="btn" style="margin-top: 1rem;">← Optimize Another Job</a>
</div>
{% endblock %}'''
    
    (templates_dir / 'ats_result.html').write_text(ats_result_template)
    
    # Contacts template
    contacts_template = '''{% extends "base.html" %}

{% block title %}Contacts - InternMailer{% endblock %}

{% block content %}
<div class="card">
    <h2>📇 Contacts</h2>
    <p>Manage your contact list for email campaigns.</p>
</div>

<div class="card">
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for contact in contacts %}
            <tr>
                <td>{{ contact.name }}</td>
                <td>{{ contact.email }}</td>
                <td>{{ contact.company }}</td>
                <td>
                    {% if contact.contacted %}
                    <span class="status-badge status-success">Contacted</span>
                    {% else %}
                    <span class="status-badge status-warning">Not Contacted</span>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="4" style="text-align: center; color: #666;">No contacts found. Add contacts to your database.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''
    
    (templates_dir / 'contacts.html').write_text(contacts_template)
    
    # Replies template
    replies_template = '''{% extends "base.html" %}

{% block title %}Replies - InternMailer{% endblock %}

{% block content %}
<div class="card">
    <h2>📬 Replies</h2>
    <p>Monitor and manage replies to your email campaigns.</p>
</div>

<div class="card">
    <table>
        <thead>
            <tr>
                <th>From</th>
                <th>Subject</th>
                <th>Date</th>
                <th>Category</th>
                <th>Sentiment</th>
            </tr>
        </thead>
        <tbody>
            {% for reply in replies %}
            <tr>
                <td>{{ reply.sender }}</td>
                <td>{{ reply.subject }}</td>
                <td>{{ reply.date }}</td>
                <td><span class="status-badge">{{ reply.category }}</span></td>
                <td>{{ reply.sentiment }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="5" style="text-align: center; color: #666;">No replies found yet.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''
    
    (templates_dir / 'replies.html').write_text(replies_template)
    
    # Settings template
    settings_template = '''{% extends "base.html" %}

{% block title %}Settings - InternMailer{% endblock %}

{% block content %}
<div class="card">
    <h2>⚙️ Settings</h2>
    <p>View and manage your InternMailer configuration.</p>
</div>

<div class="card">
    <h3>Current Configuration</h3>
    <table>
        <tr>
            <td>Gmail User</td>
            <td>{{ config.gmail_user or 'Not set' }}</td>
        </tr>
        <tr>
            <td>Groq API Key</td>
            <td>{{ config.groq_key or 'Not set' }}</td>
        </tr>
        <tr>
            <td>Max Emails Per Day</td>
            <td>{{ config.max_emails_per_day }}</td>
        </tr>
        <tr>
            <td>Follow-up Days</td>
            <td>{{ config.followup_days }}</td>
        </tr>
    </table>
    
    <div style="margin-top: 1.5rem;">
        <p style="color: #666; margin-bottom: 1rem;">
            To change settings, edit the <code>.env</code> file in your project directory and restart the dashboard.
        </p>
        <a href="{{ url_for('index') }}" class="btn">← Back to Dashboard</a>
    </div>
</div>
{% endblock %}'''
    
    (templates_dir / 'settings.html').write_text(settings_template)
    
    print(f"✅ Created web dashboard templates in {templates_dir}")

# ============== MAIN ==============

if __name__ == '__main__':
    # Create templates
    create_templates()
    
    print("=" * 60)
    print("🌐 InternMailer Web Dashboard")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Open http://localhost:5000 in your browser\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
