#!/bin/bash
# Production startup script for Render.com

set -e

echo "🚀 Starting Fulfil Product Importer..."

# Create uploads directory
mkdir -p uploads

# Initialize database
echo "🗄️ Initializing database..."
python -c "
import asyncio
from app.db.database import init_db

async def setup():
    try:
        await init_db()
        print('✅ Database initialized successfully')
    except Exception as e:
        print(f'⚠️ Database initialization warning: {e}')

asyncio.run(setup())
"

# Start Celery worker in background
echo "⚙️ Starting background worker..."
celery -A app.tasks.import_tasks worker --loglevel=info --concurrency=1 &

# Give worker a moment to start
sleep 3

# Start web server
echo "🌐 Starting web server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}