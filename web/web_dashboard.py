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
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from typing import Optional

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for, send_file
from flask import session
from werkzeug.utils import secure_filename

# Set up logging
logger = logging.getLogger(__name__)

# Import flask-cors for proper CORS handling
try:
    from flask_cors import CORS
except ImportError:
    print("⚠️ flask-cors not installed. Turning off CORS support.")
    CORS = None

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.config import config
from core.database_manager import get_job_discovery_db
from core.resume_service import optimize_for_job
from middleware.csrf import init_csrf
from middleware.rate_limit import RateLimiter, rate_limit
from middleware.health_check import get_health_checker, get_metrics_collector

try:
    from web.ai_resume import extract_text_from_pdf, extract_json_payload
except ImportError:
    # Fallback if ai_resume.py is missing or broken
    def extract_text_from_pdf(path): return ""
    def extract_json_payload(text): return {}

# Import InternMailer components
try:
    from core.email_system import EmailSystem
    from core.unified_ai_provider import get_unified_ai_provider
    EMAIL_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Email system not available: {e}")
    EMAIL_SYSTEM_AVAILABLE = False

# Job discovery/apply
try:
    from core.job_discovery import JobDiscovery
    from core.job_pipeline import JobPipeline
    JOBS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Job discovery not available: {e}")
    JOBS_AVAILABLE = False

try:
    from core.market_sentiment import get_market_sentiment_engine
    MARKET_SENTIMENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Market sentiment not available: {e}")
    MARKET_SENTIMENT_AVAILABLE = False

app = Flask(__name__, template_folder='../templates/web')
app.secret_key = config.SECRET_KEY if 'config' in globals() else os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config.update(
    SESSION_COOKIE_SECURE=config.SESSION_SECURE,
    SESSION_COOKIE_HTTPONLY=config.SESSION_HTTPONLY,
    SESSION_COOKIE_SAMESITE=config.SESSION_SAMESITE
)

# Enable CORS
if CORS:
    # Allow requests from frontend origin
    origin = config.FRONTEND_ORIGIN or 'http://localhost:5173'
    CORS(app, resources={r"/api/*": {"origins": origin}})

# Security middleware
csrf = init_csrf(app) if config.CSRF_ENABLED else None
rate_limiter = RateLimiter(
    requests_per_minute=config.RATE_LIMIT_PER_MINUTE,
    requests_per_hour=config.RATE_LIMIT_PER_HOUR,
    requests_per_day=config.RATE_LIMIT_PER_DAY
)

@app.before_request
def apply_rate_limits():
    if request.path.startswith('/api'):
        allowed, info = rate_limiter.is_allowed(request)
        if not allowed:
            return jsonify({
                'status': 'error',
                'message': 'Rate limit exceeded',
                'limit_type': info.get('limit_type'),
                'retry_after': info.get('retry_after')
            }), 429


def call_groq(prompt: str) -> str:
    if not config.GROQ_API_KEY:
        raise RuntimeError('GROQ_API_KEY not configured')

    payload = {
        'model': config.GROQ_MODEL or 'llama-3.1-8b-instant',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7
    }
    headers = {
        'Authorization': f'Bearer {config.GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=30
    )
    if response.status_code >= 400:
        raise RuntimeError(f'Groq API error: {response.status_code}')
    data = response.json()
    return data['choices'][0]['message']['content'].strip()

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
    
    # Get daemon status
    daemon_status_info = {
        'running': False,
        'pid': None
    }
    if daemon_process and daemon_process.poll() is None:
        daemon_status_info['running'] = True
        daemon_status_info['pid'] = daemon_process.pid
    
    return render_template('dashboard.html', stats=stats, daemon_status=daemon_status_info)

@app.route('/test-buttons')
def test_buttons():
    """Test page for button functionality"""
    return render_template('test_buttons.html')

@app.route('/api/stats')
def api_stats():
    """Get current campaign statistics"""
    return jsonify(get_campaign_stats())

@app.route('/api/contacts/available')
def contacts_available():
    """Check how many fresh contacts are available"""
    try:
        from core.email_system import EmailSystem
        system = EmailSystem()
        contacts = system.get_fresh_contacts(count=100)  # Check up to 100
        
        return jsonify({
            'status': 'success',
            'available': len(contacts),
            'message': f'{len(contacts)} fresh contacts available' if len(contacts) > 0 else 'No fresh contacts available. Add more contacts or reset sent status.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'available': 0,
            'message': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    checker = get_health_checker()
    return jsonify(checker.run_all_checks())

@app.route('/metrics')
def metrics():
    """Metrics endpoint"""
    collector = get_metrics_collector()
    return jsonify(collector.get_metrics())

@app.route('/send-emails', methods=['POST'])
@rate_limit(requests_per_minute=2, requests_per_hour=10)  # Strict limit for email sending
def send_emails():
    """Send emails via API"""
    from utils.security import InputValidator
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json(silent=True) or {}
    count_raw = data.get('count', 10)
    
    # Validate and sanitize count
    count = InputValidator.validate_positive_int(count_raw, max_value=100)
    if count is None:
        return jsonify({'error': 'count must be a positive integer between 1 and 100'}), 400
    
    result_container = {'sent': 0, 'failed': 0, 'error': None}
    
    def send_task():
        try:
            system = EmailSystem()
            result = system.send_campaign(count=count)
            result_container['sent'] = result.get('sent', 0)
            result_container['failed'] = result.get('failed', 0)
            campaign_stats['emails_sent'] += result.get('sent', 0)
            campaign_stats['emails_failed'] += result.get('failed', 0)
            campaign_stats['last_updated'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error sending emails: {e}", exc_info=True)
            result_container['error'] = 'Internal server error'
    
    # Run in background thread
    thread = threading.Thread(target=send_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started', 
        'count': count,
        'message': f'Email campaign started for {count} contacts'
    })

@app.route('/preview-emails', methods=['GET'])
def preview_emails():
    """Get email previews"""
    try:
        count_raw = request.args.get('count', 3)
        
        # Validate count
        from utils.security import InputValidator
        count = InputValidator.validate_positive_int(count_raw, max_value=10) or 3
        
        system = EmailSystem()
        previews = system.preview(count=count)
        return jsonify({'status': 'success', 'previews': previews})
    except Exception as e:
        logger.error(f"Error previewing emails: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to preview emails'}), 500


@app.route('/api/ai/cover-letter', methods=['POST', 'OPTIONS'])
@rate_limit(requests_per_minute=10, requests_per_hour=100)
def ai_cover_letter():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    from utils.security import InputValidator, require_json, validate_input
    
    @require_json
    def _handle():
        data = request.get_json(silent=True) or {}
        
        # Sanitize and validate input
        role = InputValidator.sanitize_string(data.get('role', ''), max_length=200)
        company = InputValidator.sanitize_string(data.get('company', ''), max_length=200)
        skills = InputValidator.sanitize_string(data.get('skills', ''), max_length=1000)
        
        if not role or not company:
            return jsonify({'error': 'role and company are required'}), 400
        
        # Prevent prompt injection by sanitizing
        prompt = (
            f"Write a passionate cover letter for {role} at {company} based on my skills: {skills}."
            " Keep it concise, professional, and focused on impact."
        )
        
        try:
            text = call_groq(prompt)
            return jsonify({'text': text})
        except Exception as e:
            logger.error(f"AI cover letter generation failed: {e}")
            return jsonify({'error': 'Failed to generate cover letter'}), 500
    
    return _handle()


@app.route('/api/ai/interview-guide', methods=['POST', 'OPTIONS'])
@rate_limit(requests_per_minute=10, requests_per_hour=100)
def ai_interview_guide():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    from utils.security import InputValidator, require_json
    
    @require_json
    def _handle():
        data = request.get_json(silent=True) or {}
        
        # Sanitize and validate input
        role = InputValidator.sanitize_string(data.get('role', ''), max_length=200)
        company = InputValidator.sanitize_string(data.get('company', ''), max_length=200)
        skills = InputValidator.sanitize_string(data.get('skills', ''), max_length=1000)
        
        if not role or not company:
            return jsonify({'error': 'role and company are required'}), 400
        
        prompt = (
            f"Create a focused interview guide for {role} at {company}, based on my skills: {skills}."
            " Include 5 technical topics, 3 behavioral prompts, and a short prep checklist."
        )
        
        try:
            text = call_groq(prompt)
            return jsonify({'text': text})
        except Exception as e:
            logger.error(f"AI interview guide generation failed: {e}")
            return jsonify({'error': 'Failed to generate interview guide'}), 500
    
    return _handle()


@app.route('/api/ai/analyze-resume', methods=['POST', 'OPTIONS'])
def ai_analyze_resume():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    if 'file' not in request.files:
        return jsonify({'message': 'file is required'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'message': 'invalid file'}), 400

    filename = secure_filename(file.filename)
    ext = Path(filename).suffix.lower()
    if ext != '.pdf':
        return jsonify({'message': 'Only PDF resumes are supported in free mode.'}), 400

    tmp_dir = Path('tmp')
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / f'upload_{int(time.time())}.pdf'
    file.save(tmp_path)

    try:
        text = extract_text_from_pdf(tmp_path)
        prompt = (
            "Analyze this resume text and return ONLY valid JSON matching this schema: "
            "{ fullName: string, summary: string, experience: [{title, content, date}], "
            "education: [{title, content, date}], projects: [{name, description, tech: string[]}], "
            "skills: string, avatar: string }. "
            "Improve wording to be action-oriented. Resume text: "
            f"\n\n{text}"
        )
        ai_text = call_groq(prompt)
        payload = extract_json_payload(ai_text)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.route('/api/ai/claire', methods=['POST', 'OPTIONS'])
def ai_claire():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    stats = data.get('stats', {})
    skills = data.get('skills', '')

    if not message:
        return jsonify({'message': 'message is required'}), 400

    applied = stats.get('applied', 0)
    interviews = stats.get('interviews', 0)
    offers = stats.get('offers', 0)
    conversion = (interviews / applied * 100) if applied else 0

    prompt = (
        "You are Claire, a friendly and empathetic career coach."
        " Provide concise, actionable guidance."
        f" Stats: applied={applied}, interviews={interviews}, offers={offers}, conversion_rate={conversion:.1f}%."
        f" Candidate skills: {skills}."
        f" User message: {message}"
    )
    try:
        text = call_groq(prompt)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

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
            result = optimize_for_job(
                job_description,
                company_name=company_name,
                position=request.form.get('position_title', 'Position'),
            )
            
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
    stats = {
        'total': len(contacts) if contacts else 0,
        'sent': sum(1 for c in contacts if c.get('status') == 'sent') if contacts else 0,
        'replies': sum(1 for c in contacts if c.get('status') == 'replied') if contacts else 0,
        'followups': sum(1 for c in contacts if c.get('status') == 'followed_up') if contacts else 0
    }
    return render_template('contacts.html', contacts=contacts, stats=stats)

@app.route('/replies')
def replies_page():
    """Replies monitoring page"""
    replies = get_replies()
    stats = {
        'total': len(replies) if replies else 0,
        'interested': sum(1 for r in replies if r.get('classification') == 'INTERESTED') if replies else 0,
        'not_interested': sum(1 for r in replies if r.get('classification') == 'NOT_INTERESTED') if replies else 0,
        'questions': sum(1 for r in replies if r.get('classification') == 'QUESTION') if replies else 0
    }
    return render_template('replies.html', replies=replies, stats=stats)

@app.route('/settings')
def settings_page():
    """Settings page"""
    config = get_current_config()
    return render_template('settings.html', config=config)

@app.route('/jobs')
def jobs_page():
    """Job discovery page"""
    jobs = get_jobs(limit=100)
    stats = get_job_stats()
    return render_template('jobs.html', jobs=jobs, stats=stats)

@app.route('/sentiment')
def sentiment_page():
    """Market sentiment dashboard page"""
    snapshot = get_market_sentiment_snapshot()
    history = get_market_sentiment_history(limit=8)
    return render_template('sentiment.html', snapshot=snapshot, history=history)

@app.route('/api/sentiment/snapshot')
def api_sentiment_snapshot():
    """Get current market sentiment snapshot"""
    try:
        return jsonify(get_market_sentiment_snapshot())
    except Exception as e:
        logger.error(f"Error getting sentiment snapshot: {e}", exc_info=True)
        # Keep the endpoint stable for the UI/tests even when the engine is unavailable.
        return jsonify({
            "status": "error",
            "message": "Failed to retrieve market sentiment snapshot",
        }), 200

@app.route('/api/sentiment/refresh', methods=['POST'])
@rate_limit(requests_per_minute=10, requests_per_hour=100)
def api_sentiment_refresh():
    """Trigger a background refresh of market sentiment signals"""
    data = request.get_json(silent=True) or {}

    # Optional watchlist override (comma-separated string or list)
    symbols_raw = data.get("symbols", None)
    symbols = None
    try:
        from utils.security import InputValidator
        if isinstance(symbols_raw, str):
            cleaned = InputValidator.sanitize_string(symbols_raw, max_length=200)
            symbols = [s.strip().upper() for s in cleaned.split(",") if s.strip()]
        elif isinstance(symbols_raw, list):
            symbols = [
                InputValidator.sanitize_string(s, max_length=16).strip().upper()
                for s in symbols_raw
                if s is not None
            ]
            symbols = [s for s in symbols if s]
    except Exception:
        # If validation tooling changes, keep refresh robust.
        symbols = None

    def refresh_task():
        try:
            engine = get_market_sentiment_engine()
            if not engine:
                logger.info("Market sentiment refresh skipped: engine not available")
                return

            # Be permissive about the engine interface for prototyping.
            if hasattr(engine, "refresh"):
                try:
                    engine.refresh(symbols=symbols)
                except TypeError:
                    engine.refresh(symbols)
            elif hasattr(engine, "run"):
                try:
                    engine.run(symbols=symbols)
                except TypeError:
                    engine.run(symbols)
        except Exception as e:
            logger.error(f"Market sentiment refresh failed: {e}", exc_info=True)

    thread = threading.Thread(target=refresh_task)
    thread.daemon = True
    thread.start()

    # Always return 200 so the UI can show a graceful message when the engine is missing.
    return jsonify({
        "status": "started",
        "message": "Market sentiment refresh started in background",
        "symbols": symbols or [],
    })


@app.route('/api/sentiment/history', methods=['GET'])
def api_sentiment_history():
    """Return recent market sentiment snapshots."""
    try:
        from utils.security import InputValidator
        limit = InputValidator.validate_positive_int(request.args.get('limit', 12), max_value=25) or 12
        history = get_market_sentiment_history(limit=limit)
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        logger.error(f"Error fetching sentiment history: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to retrieve sentiment history'}), 500

@app.route('/api/jobs', methods=['GET'])
def api_jobs():
    """List jobs"""
    try:
        status = request.args.get('status')
        limit_raw = request.args.get('limit', 100)
        
        # Validate limit
        from utils.security import InputValidator
        limit = InputValidator.validate_positive_int(limit_raw, max_value=1000) or 100
        
        jobs = get_jobs(limit=limit, status=status)
        return jsonify({'status': 'success', 'jobs': jobs})
    except Exception as e:
        logger.error(f"Error getting jobs: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to retrieve jobs'}), 500

@app.route('/api/jobs/discover', methods=['POST'])
def api_jobs_discover():
    """Run job discovery"""
    if not JOBS_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Job discovery not available'}), 500

    def discover_task():
        try:
            discovery = JobDiscovery()
            result = discovery.run()
            logger.info(f"Job discovery completed: {result}")
        except Exception as e:
            logger.error(f"Job discovery failed: {e}", exc_info=True)

    thread = threading.Thread(target=discover_task)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': 'Job discovery started in background'})

@app.route('/api/jobs/apply', methods=['POST'])
def api_jobs_apply():
    """Auto-apply to jobs"""
    if not JOBS_AVAILABLE:
        return jsonify({'status': 'error', 'message': 'Job pipeline not available'}), 500

    try:
        data = request.get_json(silent=True) or {}
        limit_raw = data.get('limit', config.JOB_DISCOVERY_DAILY_CAP)
        
        # Validate limit
        from utils.security import InputValidator
        limit = InputValidator.validate_positive_int(limit_raw, max_value=100) or config.JOB_DISCOVERY_DAILY_CAP

        def apply_task():
            try:
                pipeline = JobPipeline()
                result = pipeline.apply_pending(limit=limit)
                logger.info(f"Job apply completed: {result}")
            except Exception as e:
                logger.error(f"Job apply failed: {e}", exc_info=True)

        thread = threading.Thread(target=apply_task)
        thread.daemon = True
        thread.start()

        return jsonify({'status': 'started', 'limit': limit, 'message': 'Job application started in background'})
    except Exception as e:
        logger.error(f"Error starting job apply: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to start job application'}), 500

@app.route('/api/contacts/discover', methods=['POST'])
def api_discover_contacts():
    """Discover company contacts using Hunter.io and other sources"""
    data = request.json or {}
    custom_domains = data.get('domains', [])
    daily_cap = data.get('cap', 50)
    
    # Curated list of major tech companies hiring interns/engineers
    default_domains = [
        # FAANG + Big Tech
        'google.com', 'amazon.com', 'microsoft.com', 'apple.com', 'meta.com',
        'netflix.com', 'nvidia.com', 'salesforce.com', 'adobe.com', 'oracle.com',
        # Fast-growing Tech
        'stripe.com', 'shopify.com', 'databricks.com', 'snowflake.com',
        'datadog.com', 'cloudflare.com', 'figma.com', 'notion.so',
        'atlassian.com', 'twilio.com', 'square.com', 'coinbase.com',
        # Indian IT & Tech
        'infosys.com', 'wipro.com', 'tcs.com', 'hcltech.com',
        'zoho.com', 'freshworks.com', 'razorpay.com', 'cred.club',
        'swiggy.com', 'zomato.com', 'flipkart.com', 'phonepe.com',
        # Startups & Mid-size
        'github.com', 'gitlab.com', 'vercel.com', 'supabase.com',
        'linear.app', 'retool.com', 'plaid.com', 'brex.com',
    ]
    
    domains = custom_domains if custom_domains else default_domains
    
    def discover_task():
        try:
            from core.lead_discovery import EnhancedLeadDiscovery
            discovery = EnhancedLeadDiscovery()
            result = discovery.discover(
                domains=domains,
                daily_cap=daily_cap,
                prioritize_hiring_managers=True
            )
            logger.info(f"✅ Contact discovery complete: {result}")
        except Exception as e:
            logger.error(f"❌ Contact discovery failed: {e}", exc_info=True)
    
    thread = threading.Thread(target=discover_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'success',
        'message': f'Discovering contacts from {len(domains)} company domains using Hunter.io...',
        'domains_count': len(domains),
        'daily_cap': daily_cap
    })

@app.route('/api/test-groq')
def test_groq():
    """Test Groq API connection"""
    try:
        from core.unified_ai_provider import get_unified_ai_provider
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
        daemon_env = os.environ.copy()
        daemon_process = subprocess.Popen(
            [sys.executable, 'core/enhanced_daemon.py', '--start'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(BASE_DIR),
            env=daemon_env
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
        return jsonify({'status': 'running', 'pid': daemon_process.pid})
    else:
        return jsonify({'status': 'stopped'})

@app.route('/api/core/verify')
def core_verify_endpoint():
    """Diamond Test Suite - Run integration tests from within the app"""
    from tests.test_integration_comprehensive import TestAgentFramework, TestLeadDiscovery, TestGmailAgent, TestEnhancedDaemon
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # 1. Agent Framework
    try:
        tester = TestAgentFramework()
        tester.test_agent_context_creation()
        tester.test_orchestrator_initialization()
        results['tests']['agent_framework'] = 'pass'
    except Exception as e:
        import traceback
        traceback.print_exc()
        results['tests']['agent_framework'] = f'fail: {e}'
        
    # 2. Daemon
    try:
        tester = TestEnhancedDaemon()
        tester.test_daemon_initialization()
        tester.test_health_monitor()
        results['tests']['daemon_core'] = 'pass'
    except Exception as e:
        import traceback
        traceback.print_exc()
        results['tests']['daemon_core'] = f'fail: {e}'

    # 3. AI Ping
    try:
        results['tests']['ai_ping'] = 'pass' if config.GROQ_API_KEY else 'fail: missing key'
    except Exception as e:
        results['tests']['ai_ping'] = f'error: {e}'

    return jsonify(results)

@app.route('/api/activity')
def api_activity():
    """Get real activity logs from agents.db"""
    activities = []
    try:
        db_path = config.AGENTS_DB_PATH
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT created_at, action, status, message 
                FROM agent_logs 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            for row in cursor.fetchall():
                # Convert timestamp to relative time (simplified)
                activities.append({
                    'time': row[0],
                    'activity': row[1].replace('_', ' ').capitalize(),
                    'status': 'success' if row[2] == 'success' else 'info',
                    'details': row[3]
                })
            conn.close()
    except Exception as e:
        logger.error(f"Error getting activity: {e}", exc_info=True)
    
    # Fallback if empty
    if not activities:
        activities = [{'time': 'Just now', 'activity': 'System ready', 'status': 'info', 'details': 'Awaiting first task...'}]
        
    return jsonify(activities)

@app.route('/api/core/env-check')
def env_check():
    """Check if server can read .env and its keys"""
    shadow_env = '/tmp/internmailer_db/.env'
    project_env = os.path.join(str(BASE_DIR), '.env')
    
    # Determine which .env is in use
    env_path = shadow_env if os.path.exists(shadow_env) else project_env
    
    try:
        env_exists = os.path.exists(env_path)
    except (PermissionError, OSError):
        env_exists = False
    
    try:
        profile_exists = os.path.exists(config.PROFILE_PATH) if config.PROFILE_PATH else False
    except (PermissionError, OSError):
        profile_exists = False
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'dot_env_exists': env_exists,
        'dot_env_path': env_path,
        'profile_exists': profile_exists,
        'profile_path': config.PROFILE_PATH,
        'database_dir_exists': os.path.exists(os.path.dirname(config.DATABASE_PATH)),
        'database_dir_path': os.path.dirname(config.DATABASE_PATH),
        'keys': {}
    }
    
    # Check specific keys (masked)
    keys_to_check = ['GMAIL_USER', 'GROQ_API_KEY', 'GITHUB_TOKEN']
    for k in keys_to_check:
        val = os.environ.get(k) or config.__dict__.get(k)
        if not val:
            val = getattr(config, k, None)
            
        results['keys'][k] = 'present' if val and len(str(val)) > 5 else 'missing'
    
    # Try reading .env file
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
            results['dot_env_readable'] = True
            results['dot_env_line_count'] = len(lines)
    except Exception as e:
        results['dot_env_readable'] = f'fail: {e}'

    return jsonify(results)

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download optimized files"""
    safe_filename = secure_filename(filename)
    # Use parent directory's optimized_documents folder
    file_path = Path(__file__).parent.parent / 'optimized_documents' / safe_filename
    
    if file_path.exists():
        return send_file(str(file_path), as_attachment=True)
    else:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404

# ============== HELPER FUNCTIONS ==============

def _empty_market_sentiment_snapshot():
    return {
        'id': None,
        'created_at': None,
        'overall_score': 0.0,
        'label': 'Neutral',
        'bullish_count': 0,
        'bearish_count': 0,
        'neutral_count': 0,
        'article_count': 0,
        'entity_count': 0,
        'watchlist': [],
        'entities': [],
        'items': [],
        'summary': {
            'tracked_symbols': 0,
            'tracked_topics': 0,
            'overall_score': 0.0,
            'overall_label': 'Neutral',
            'top_positive': [],
            'top_negative': [],
            'most_bullish_entity': None,
            'most_bearish_entity': None,
        },
    }


def get_market_sentiment_snapshot():
    """Get the latest market sentiment snapshot from the engine."""
    try:
        if not MARKET_SENTIMENT_AVAILABLE:
            return _empty_market_sentiment_snapshot()
        engine = get_market_sentiment_engine()
        snapshot = engine.get_latest_snapshot()
        return snapshot or _empty_market_sentiment_snapshot()
    except Exception as e:
        logger.error(f"Error getting market sentiment snapshot: {e}", exc_info=True)
        return _empty_market_sentiment_snapshot()


def get_market_sentiment_history(limit: int = 8):
    """Get recent market sentiment history."""
    try:
        if not MARKET_SENTIMENT_AVAILABLE:
            return []
        engine = get_market_sentiment_engine()
        return engine.get_history(limit=limit)
    except Exception as e:
        logger.error(f"Error getting market sentiment history: {e}", exc_info=True)
        return []


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
        db_path = config.DATABASE_PATH
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
        logger.error(f"Error getting stats: {e}", exc_info=True)
    
    # Add in-memory stats
    stats['emails_sent'] += campaign_stats['emails_sent']
    stats['emails_failed'] += campaign_stats['emails_failed']
    stats['replies_received'] += campaign_stats['replies_received']
    
    return stats

def get_contacts():
    """Get contacts from company contacts CSV and/or database"""
    contacts = []
    seen_emails = set()
    
    # 1. Read from company contacts CSV (primary source — from lead discovery)
    try:
        csv_path = config.COMPANY_CONTACTS_CSV
        if os.path.exists(csv_path):
            import csv as csv_mod
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv_mod.DictReader(f)
                for row in reader:
                    email = (row.get('email') or '').strip().lower()
                    if email and email not in seen_emails:
                        seen_emails.add(email)
                        contacts.append({
                            'name': row.get('name', '').strip(),
                            'email': email,
                            'company': row.get('company', '').strip(),
                            'role': row.get('role', '').strip(),
                            'source': row.get('source', '').strip(),
                            'confidence': float(row.get('confidence', 0)),
                            'contacted': False,
                        })
    except Exception as e:
        logger.warning(f"Error reading company CSV: {e}", exc_info=True)
    
    # 2. Fallback: read from contacts database
    try:
        db_path = config.CONTACTS_DB_PATH
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, email, affiliation, contacted 
                FROM verified_contacts 
                LIMIT 100
            ''')
            
            for row in cursor.fetchall():
                email = (row[1] or '').strip().lower()
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    contacts.append({
                        'name': row[0],
                        'email': email,
                        'company': row[2],
                        'role': '',
                        'source': 'database',
                        'confidence': 0.5,
                        'contacted': row[3] == 'yes'
                    })
            
            conn.close()
    except Exception as e:
        logger.warning(f"Error getting contacts from DB: {e}", exc_info=True)
    
    return contacts

def get_replies():
    """Get replies from inbox monitor"""
    replies = []
    
    try:
        db_path = config.INBOX_DB_PATH
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
        logger.error(f"Error getting replies: {e}", exc_info=True)
    
    return replies

def get_current_config():
    """Get current configuration"""
    return {
        'gmail_user': os.getenv('GMAIL_USER', ''),
        'groq_key': os.getenv('GROQ_API_KEY', '')[:10] + '...' if os.getenv('GROQ_API_KEY') else '',
        'max_emails_per_day': os.getenv('MAX_EMAILS_PER_DAY', '100'),
        'followup_days': os.getenv('FOLLOWUP_DAYS', '7'),
    }

def get_jobs(limit: int = 100, status: Optional[str] = None):
    """Get jobs from job discovery database"""
    try:
        db = get_job_discovery_db(config.JOBS_DB_PATH)
        if status:
            rows = db.fetch_all(
                "SELECT * FROM jobs WHERE status = ? ORDER BY score DESC LIMIT ?",
                (status, limit),
            )
        else:
            rows = db.fetch_all(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting jobs: {e}", exc_info=True)
        return []

def get_job_stats():
    """Get job discovery stats"""
    try:
        db = get_job_discovery_db(config.JOBS_DB_PATH)
        total = db.fetch_one("SELECT COUNT(*) as count FROM jobs")
        applied = db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE status = 'applied'")
        pending = db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE status = 'new'")
        return {
            'total': total['count'] if total else 0,
            'applied': applied['count'] if applied else 0,
            'pending': pending['count'] if pending else 0,
        }
    except Exception as e:
        logger.error(f"Error getting job stats: {e}", exc_info=True)
        return {'total': 0, 'applied': 0, 'pending': 0}


_SENTIMENT_ENGINE = None
_SENTIMENT_ENGINE_INIT = False


def _load_market_sentiment_engine():
    """
    Lazy-load the sentiment engine so the dashboard can still boot without it.

    Worker-1 will provide the core module; until then this returns None.
    """
    global _SENTIMENT_ENGINE, _SENTIMENT_ENGINE_INIT
    if _SENTIMENT_ENGINE_INIT:
        return _SENTIMENT_ENGINE
    _SENTIMENT_ENGINE_INIT = True

    try:
        from core.market_sentiment import get_market_sentiment_engine as _core_get_engine  # type: ignore
        _SENTIMENT_ENGINE = _core_get_engine()
        return _SENTIMENT_ENGINE
    except Exception:
        pass

    try:
        from core.market_sentiment import MarketSentimentEngine  # type: ignore
        _SENTIMENT_ENGINE = MarketSentimentEngine()
        return _SENTIMENT_ENGINE
    except Exception:
        _SENTIMENT_ENGINE = None
        return None


def get_market_sentiment_engine():
    """
    Public accessor used by the dashboard and tests.

    This can be monkeypatched in tests to avoid importing the real engine.
    """
    return _load_market_sentiment_engine()


def get_market_sentiment_snapshot(symbols: Optional[list[str]] = None) -> dict:
    """Best-effort combined snapshot used by both the page and JSON endpoints."""
    snapshot = {
        "status": "unavailable",
        "as_of": datetime.now().isoformat(),
        "overall_score": 0.0,
        "overall_label": "Neutral",
        "label": "Neutral",
        "created_at": datetime.now().isoformat(),
        "summary": {
            "tracked_topics": 0,
            "tracked_symbols": 0,
            "overall_score": 0.0,
            "overall_label": "Neutral",
            "top_positive": [],
            "top_negative": [],
            "most_bullish_entity": None,
            "most_bearish_entity": None,
        },
        "article_count": 0,
        "entity_count": 0,
        "bullish_count": 0,
        "bearish_count": 0,
        "neutral_count": 0,
        "entities": [],
        "sources": [],
        "items": [],
        "watchlist": [],
        "symbols": symbols or [],
        "message": "Market sentiment engine not configured yet.",
    }

    engine = get_market_sentiment_engine()
    if not engine:
        return snapshot

    try:
        topics = [str(topic).strip() for topic in (symbols or []) if str(topic).strip()]
        if not topics and hasattr(engine, "store") and hasattr(engine.store, "list_topics"):
            topics = list(engine.store.list_topics())

        if hasattr(engine, "get_snapshot"):
            try:
                topic_snapshots = engine.get_snapshot(topics=topics or None)
            except TypeError:
                topic_snapshots = engine.get_snapshot(topics or None)
        elif hasattr(engine, "snapshot"):
            try:
                topic_snapshots = engine.snapshot(topics=topics or None)
            except TypeError:
                topic_snapshots = engine.snapshot(topics or None)
        else:
            return snapshot

        if hasattr(topic_snapshots, "to_dict"):
            topic_snapshots = topic_snapshots.to_dict()
        if not isinstance(topic_snapshots, dict) or not topic_snapshots:
            snapshot["status"] = "success"
            return snapshot

        combined_entities = []
        combined_items = []
        score_weight = 0.0
        weight_total = 0.0
        bullish = bearish = neutral = 0
        latest_as_of = None

        def _sentiment_value(item: dict) -> float:
            value = item.get("sentiment_score", item.get("sentiment", 0.0))
            try:
                return float(value)
            except Exception:
                return 0.0

        for topic, snap in topic_snapshots.items():
            if not isinstance(snap, dict):
                continue

            items = snap.get("items") or []
            item_count = int(snap.get("item_count") or len(items) or 0)
            score = float(snap.get("score", snap.get("overall_score", 0.0)) or 0.0)
            computed_at = snap.get("computed_at") or snap.get("created_at") or snap.get("as_of")
            if computed_at and (latest_as_of is None or str(computed_at) > str(latest_as_of)):
                latest_as_of = computed_at

            normalized_items = []
            confidences = []
            for item in items:
                sent = _sentiment_value(item)
                conf = float(item.get("confidence", 0.0) or 0.0)
                confidences.append(conf)
                normalized_item = {
                    "topic": topic,
                    "entity": topic,
                    "source": item.get("source", ""),
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("url", ""),
                    "published_at": item.get("published_at"),
                    "sentiment_score": sent,
                    "confidence": conf,
                    "metadata": item.get("raw", {}),
                }
                normalized_items.append(normalized_item)
                combined_items.append(normalized_item)
                if sent > 0.15:
                    bullish += 1
                elif sent < -0.15:
                    bearish += 1
                else:
                    neutral += 1

            avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
            entity = {
                "entity": topic,
                "label": topic,
                "type": "topic",
                "symbol": None,
                "item_count": item_count,
                "news_score": score,
                "momentum_score": 0.0,
                "combined_score": score,
                "confidence": round(avg_confidence, 3),
                "bullish_count": int(snap.get("positive", 0) or 0),
                "bearish_count": int(snap.get("negative", 0) or 0),
                "neutral_count": int(snap.get("neutral", 0) or 0),
                "top_headlines": normalized_items[:3],
            }
            combined_entities.append(entity)

            score_weight += score * max(item_count, 1)
            weight_total += max(item_count, 1)

        overall_score = (score_weight / weight_total) if weight_total else 0.0
        if overall_score >= 0.2:
            overall_label = "Bullish"
        elif overall_score <= -0.2:
            overall_label = "Bearish"
        else:
            overall_label = "Neutral"

        top_positive = sorted(
            combined_items,
            key=lambda item: (item.get("sentiment_score", 0.0), item.get("confidence", 0.0)),
            reverse=True,
        )[:5]
        top_negative = sorted(
            combined_items,
            key=lambda item: (item.get("sentiment_score", 0.0), item.get("confidence", 0.0)),
        )[:5]

        most_bullish = max(combined_entities, key=lambda item: item.get("combined_score", 0.0), default=None)
        most_bearish = min(combined_entities, key=lambda item: item.get("combined_score", 0.0), default=None)

        snapshot.update({
            "status": "success",
            "as_of": str(latest_as_of or datetime.now().isoformat()),
            "created_at": str(latest_as_of or datetime.now().isoformat()),
            "overall_score": round(overall_score, 3),
            "overall_label": overall_label,
            "label": overall_label,
            "sources": [entity["label"] for entity in combined_entities],
            "watchlist": [{"type": "topic", "value": entity["label"], "label": entity["label"]} for entity in combined_entities],
            "entities": combined_entities,
            "items": combined_items,
            "article_count": len(combined_items),
            "entity_count": len(combined_entities),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "summary": {
                "tracked_topics": len(combined_entities),
                "tracked_symbols": sum(1 for topic in topics if str(topic).upper() == str(topic) and len(str(topic)) <= 6),
                "overall_score": round(overall_score, 3),
                "overall_label": overall_label,
                "top_positive": top_positive,
                "top_negative": top_negative,
                "most_bullish_entity": most_bullish,
                "most_bearish_entity": most_bearish,
            },
            "message": "Market sentiment snapshot ready",
        })
        return snapshot
    except Exception as e:
        logger.error(f"Error building sentiment snapshot: {e}", exc_info=True)
        snapshot["status"] = "error"
        snapshot["message"] = "Market sentiment engine error"
        return snapshot


def get_market_sentiment_history(limit: int = 12) -> list[dict]:
    """Best-effort history list for templates; safe to call without engine."""
    engine = get_market_sentiment_engine()
    if not engine:
        return []

    try:
        if hasattr(engine, "store") and hasattr(engine.store, "get_history"):
            rows = engine.store.get_history(limit=limit)
        elif hasattr(engine, "get_history"):
            rows = engine.get_history(limit=limit)
        elif hasattr(engine, "history"):
            rows = engine.history(limit=limit)
        else:
            return []

        if rows is None:
            return []
        if isinstance(rows, list):
            return [r.to_dict() if hasattr(r, "to_dict") else dict(r) for r in rows]
        return []
    except Exception as e:
        logger.error(f"Error getting sentiment history: {e}", exc_info=True)
        return []

# ============== MAIN ==============

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 InternMailer Web Dashboard")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Open http://localhost:5050 in your browser\n")
    
    # Run Flask app
    host = config.FLASK_HOST if 'config' in globals() else '0.0.0.0'
    port = config.FLASK_PORT if 'config' in globals() else 5000
    debug = config.DEBUG if 'config' in globals() else True
    app.run(host=host, port=port, debug=debug)
