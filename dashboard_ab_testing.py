"""
InternMailer - A/B Testing Dashboard
Real-time campaign metrics and statistical analysis
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import math

app = Flask(__name__)

def get_ab_test_stats() -> List[Dict]:
    """Get all A/B tests with statistics"""
    db_path = 'campaign_results/advanced_tracking.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT test_name, variant_a, variant_b,
               variant_a_sent, variant_a_opened,
               variant_b_sent, variant_b_opened,
               winner, created_date
        FROM ab_tests
        ORDER BY created_date DESC
    ''')
    
    tests = []
    for row in cursor.fetchall():
        test_name, var_a, var_b, a_sent, a_opened, b_sent, b_opened, winner, created = row
        
        # Calculate open rates
        a_rate = (a_opened / a_sent * 100) if a_sent > 0 else 0
        b_rate = (b_opened / b_sent * 100) if b_sent > 0 else 0
        
        # Calculate statistical significance
        significance = calculate_significance(a_sent, a_opened, b_sent, b_opened)
        
        # Determine winner if not set
        if not winner and significance['is_significant']:
            if a_rate > b_rate:
                winner = 'A'
            elif b_rate > a_rate:
                winner = 'B'
        
        tests.append({
            'test_name': test_name,
            'variant_a': var_a,
            'variant_b': var_b,
            'a_sent': a_sent,
            'a_opened': a_opened,
            'a_rate': a_rate,
            'b_sent': b_sent,
            'b_opened': b_opened,
            'b_rate': b_rate,
            'winner': winner,
            'is_significant': significance['is_significant'],
            'confidence': significance['confidence'],
            'created_date': created
        })
    
    conn.close()
    return tests

def calculate_significance(a_sent: int, a_opened: int, b_sent: int, b_opened: int) -> Dict:
    """
    Calculate statistical significance using z-test for proportions
    Returns confidence level and whether difference is significant
    """
    if a_sent == 0 or b_sent == 0:
        return {'is_significant': False, 'confidence': 0.0}
    
    p1 = a_opened / a_sent
    p2 = b_opened / b_sent
    
    # Pooled proportion
    p_pool = (a_opened + b_opened) / (a_sent + b_sent)
    
    # Standard error
    se = math.sqrt(p_pool * (1 - p_pool) * (1/a_sent + 1/b_sent))
    
    if se == 0:
        return {'is_significant': False, 'confidence': 0.0}
    
    # Z-score
    z = abs(p1 - p2) / se
    
    # Convert z-score to confidence level
    # z > 1.96 = 95% confidence, z > 2.58 = 99% confidence
    if z > 2.58:
        confidence = 0.99
        is_significant = True
    elif z > 1.96:
        confidence = 0.95
        is_significant = True
    elif z > 1.645:
        confidence = 0.90
        is_significant = False  # Not quite significant
    else:
        confidence = 0.80
        is_significant = False
    
    return {
        'is_significant': is_significant,
        'confidence': confidence,
        'z_score': z
    }

def get_campaign_metrics() -> Dict:
    """Get overall campaign metrics"""
    db_path = 'email_tracking.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total emails sent
        cursor.execute("SELECT COUNT(*) FROM sent_emails")
        total_sent = cursor.fetchone()[0]
        
        # Emails sent today
        cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE date(sent_at) = date('now')")
        sent_today = cursor.fetchone()[0]
        
        # Emails sent this week
        cursor.execute("SELECT COUNT(*) FROM sent_emails WHERE date(sent_at) > date('now', '-7 days')")
        sent_week = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sent': total_sent,
            'sent_today': sent_today,
            'sent_week': sent_week
        }
    except:
        return {'total_sent': 0, 'sent_today': 0, 'sent_week': 0}

# HTML Dashboard Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>A/B Testing Dashboard - InternMailer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .metric-value {
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .test-card {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .test-name {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }
        
        .winner-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .winner-a { background: #d4edda; color: #155724; }
        .winner-b { background: #cce5ff; color: #004085; }
        .no-winner { background: #f8d7da; color: #721c24; }
        
        .variants-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .variant {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
        }
        
        .variant.winner {
            border-color: #28a745;
            background: #f0fff4;
        }
        
        .variant-label {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .variant-text {
            color: #333;
            margin-bottom: 15px;
            font-style: italic;
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
        }
        
        .significance {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .confidence-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 20px;
        }
        
        .refresh-btn:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 A/B Testing Dashboard</h1>
            <p class="subtitle">Real-time campaign metrics & statistical analysis</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{{ metrics.total_sent }}</div>
                <div class="metric-label">Total Sent</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.sent_today }}</div>
                <div class="metric-label">Sent Today</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ metrics.sent_week }}</div>
                <div class="metric-label">This Week</div>
            </div>
        </div>
        
        {% if tests %}
            {% for test in tests %}
            <div class="test-card">
                <div class="test-header">
                    <div class="test-name">{{ test.test_name }}</div>
                    <div class="winner-badge {% if test.winner == 'A' %}winner-a{% elif test.winner == 'B' %}winner-b{% else %}no-winner{% endif %}">
                        {% if test.winner %}
                            🏆 Winner: Variant {{ test.winner }}
                        {% elif test.is_significant %}
                            ⚠️ Results Ready
                        {% else %}
                            ⏳ Testing...
                        {% endif %}
                    </div>
                </div>
                
                <div class="variants-grid">
                    <div class="variant {% if test.winner == 'A' %}winner{% endif %}">
                        <div class="variant-label">Variant A</div>
                        <div class="variant-text">"{{ test.variant_a }}"</div>
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-value">{{ test.a_sent }}</div>
                                <div class="stat-label">Sent</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ test.a_opened }}</div>
                                <div class="stat-label">Opened</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ "%.1f"|format(test.a_rate) }}%</div>
                                <div class="stat-label">Rate</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="variant {% if test.winner == 'B' %}winner{% endif %}">
                        <div class="variant-label">Variant B</div>
                        <div class="variant-text">"{{ test.variant_b }}"</div>
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-value">{{ test.b_sent }}</div>
                                <div class="stat-label">Sent</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ test.b_opened }}</div>
                                <div class="stat-label">Opened</div>
                            </div>
                            <div class="stat">
                                <div class="stat-value">{{ "%.1f"|format(test.b_rate) }}%</div>
                                <div class="stat-label">Rate</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="significance">
                    <div>Statistical Confidence: <strong>{{ "%.0f"|format(test.confidence * 100) }}%</strong></div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {{ test.confidence * 100 }}%"></div>
                    </div>
                    <small style="color: #666; margin-top: 5px; display: block;">
                        {% if test.is_significant %}
                            ✅ Results are statistically significant (95%+ confidence)
                        {% else %}
                            ⏳ Need more data for statistical significance
                        {% endif %}
                    </small>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="test-card">
                <p style="text-align: center; color: #666;">No A/B tests configured yet.</p>
            </div>
        {% endif %}
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
'''

@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Main dashboard view"""
    tests = get_ab_test_stats()
    metrics = get_campaign_metrics()
    return render_template_string(DASHBOARD_HTML, tests=tests, metrics=metrics)

@app.route('/api/tests')
def api_tests():
    """API endpoint for A/B test data"""
    tests = get_ab_test_stats()
    return jsonify(tests)

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for campaign metrics"""
    metrics = get_campaign_metrics()
    return jsonify(metrics)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'ab-testing-dashboard'}

if __name__ == '__main__':
    print("🚀 Starting A/B Testing Dashboard on http://localhost:5001")
    print("📊 Dashboard: http://localhost:5001/dashboard")
    print("🔌 API: http://localhost:5001/api/tests")
    app.run(host='0.0.0.0', port=5001, debug=False)
