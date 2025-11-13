#!/bin/bash
# Startup script for deployment platforms

set -e

echo "🚀 Starting Fulfil Product Importer..."

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

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

echo "✅ Startup complete!"