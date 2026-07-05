#!/bin/bash
# ============================================================
# InternMailer — Full Autonomous Mode
# ============================================================
# Run this script to start the fully autonomous job application
# pipeline. It discovers jobs, tailors resumes, and applies —
# all with zero manual involvement.
#
# Usage:
#   chmod +x run_full_auto.sh
#   ./run_full_auto.sh              # Start autonomous scheduler (24/7)
#   ./run_full_auto.sh --discover   # Run job discovery once
#   ./run_full_auto.sh --apply      # Run application pipeline once
#   ./run_full_auto.sh --full       # Run full pipeline once (discover + apply)
#   ./run_full_auto.sh --dashboard  # Start web dashboard only
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found. Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Copy config/.env.example to .env and configure it."
    exit 1
fi

# Add src to PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/src:$SCRIPT_DIR:$PYTHONPATH"

MODE="${1:---daemon}"

echo "🚀 InternMailer — Full Autonomous Mode"
echo "======================================="
echo "Mode: $MODE"
echo ""

case "$MODE" in
    --daemon|-d)
        echo "🤖 Starting 24/7 Autonomous Scheduler..."
        echo "   - Discovering jobs from 20+ sources"
        echo "   - Tailoring resumes with AI (Groq)"
        echo "   - Auto-applying with Playwright"
        echo "   - Rate limiting: 8/hr, 40/day"
        echo "   - Press Ctrl+C to stop"
        echo ""
        python3 -m core.autonomous_scheduler --daemon
        ;;
    --discover)
        echo "🔍 Running job discovery..."
        python3 -m core.autonomous_scheduler --discover
        ;;
    --apply)
        echo "📨 Running application pipeline..."
        python3 -m core.autonomous_scheduler --apply
        ;;
    --full)
        echo "🚀 Running full pipeline (discover + apply)..."
        python3 -m core.autonomous_scheduler --full
        ;;
    --dashboard|-w)
        echo "🌐 Starting web dashboard..."
        python3 main.py --web
        ;;
    --cli|-c)
        echo "🖥️  Starting CLI menu..."
        python3 main.py --cli
        ;;
    --validate|-v)
        echo "✅ Running validation..."
        python3 main.py --validate
        ;;
    --status)
        python3 -m core.autonomous_scheduler --status
        ;;
    --analytics)
        python3 -m core.autonomous_scheduler --analytics
        ;;
    *)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  (no args)    Start 24/7 autonomous scheduler (default)"
        echo "  --discover   Run job discovery once"
        echo "  --apply      Run application pipeline once"
        echo "  --full       Run full pipeline once (discover + apply)"
        echo "  --dashboard  Start web dashboard"
        echo "  --cli        Start CLI menu"
        echo "  --validate   Validate configuration"
        echo "  --status     Show scheduler status"
        echo "  --analytics  Show application analytics"
        ;;
esac
