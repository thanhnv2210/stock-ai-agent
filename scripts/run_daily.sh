#!/bin/bash
# Daily pipeline runner — intended for cron scheduling.
#
# Crontab setup (run weekdays at 6:00 PM local time):
#   crontab -e
#   0 18 * * 1-5 /absolute/path/to/stock-ai-agent/scripts/run_daily.sh >> /absolute/path/to/stock-ai-agent/logs/daily.log 2>&1
#
# One-time setup:
#   chmod +x scripts/run_daily.sh
#   mkdir -p logs

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Load notification env vars from .env if present
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

source "$PROJECT_DIR/venv/bin/activate"

echo "=== $(date) ==="
python -m src.jobs.daily_pipeline
