#!/bin/bash

# Production startup script for Heroku/Render deployment

# Install dependencies if not already installed
pip install --upgrade pip
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Run database migrations (if using Alembic)
# alembic upgrade head

echo "Starting Fulfil Product Importer..."
echo "Environment: ${NODE_ENV:-production}"
echo "Port: ${PORT:-8000}"

# Start the application
if [ "$DYNO" = "web.1" ] || [ "$RENDER_SERVICE_TYPE" = "web" ]; then
    echo "Starting web server..."
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
elif [ "$DYNO" = "worker.1" ] || [ "$RENDER_SERVICE_TYPE" = "worker" ]; then
    echo "Starting Celery worker..."
    celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
else
    # Default to web server
    echo "Starting web server (default)..."
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi