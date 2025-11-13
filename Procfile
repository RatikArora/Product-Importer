web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
worker: celery -A app.tasks.import_tasks worker --loglevel=info --concurrency=1
release: python -c "import asyncio; from app.db.database import init_db; asyncio.run(init_db())"