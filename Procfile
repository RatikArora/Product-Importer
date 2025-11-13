web: ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: ./venv/bin/celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2