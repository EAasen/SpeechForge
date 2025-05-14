#!/bin/bash
# diaspeak-async.sh: Helper script to run DiaSpeak Flask, Redis, and Celery for async TTS

set -e

# Start Redis (if not already running)
echo "[diaspeak-async] Starting Redis..."
docker-compose up -d redis

# Start Flask app (in background)
echo "[diaspeak-async] Starting Flask app..."
docker-compose up -d diaspeak

# Wait for Flask and Redis to be ready
sleep 5

# Start Celery worker (in a new terminal or background)
echo "[diaspeak-async] Starting Celery worker..."
docker-compose exec diaspeak celery -A src.app.celery_app worker --loglevel=info &

echo "[diaspeak-async] All services started."
echo "- Flask API:    http://localhost:8000"
echo "- Redis:        localhost:6379"
echo "- Celery worker running in diaspeak container."
echo "Use /speak-async and /job/<job_id> endpoints for async TTS."
