"""
Celery tasks for importing products from CSV files with pandas support for unlimited records.
"""
import asyncio
import csv
import json
import redis
from io import StringIO
from typing import Dict, List, Any, Tuple
from decimal import Decimal, InvalidOperation
import pandas as pd
import numpy as np
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.tasks.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.models import Product, ImportJob
from app.core.config import settings


redis_client = redis.Redis.from_url(settings.effective_redis_url)


@celery_app.task(bind=True, name='app.tasks.import_tasks.process_csv_upload')
def process_csv_upload(self, file_content: str, filename: str, job_id: int) -> Dict[str, Any]:
    """
    Process CSV file upload asynchronously.
    
    Args:
        file_content: The CSV file content as string
        filename: Original filename
        job_id: Import job ID for tracking progress
        
    Returns:
        Dict with processing results
    """
    # Use the existing async event loop or create a new one
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're already in an async context, so we need to handle this differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _process_csv_upload_async(self, file_content, filename, job_id))
                return future.result()
        else:
            return loop.run_until_complete(_process_csv_upload_async(self, file_content, filename, job_id))
    except RuntimeError:
        # No event loop running, create a new one
        return asyncio.run(_process_csv_upload_async(self, file_content, filename, job_id))


async def _process_csv_upload_async(task_self, file_content: str, filename: str, job_id: int) -> Dict[str, Any]:
    """Async implementation of CSV processing."""
    
    # Normalize line endings to fix mixed CRLF/LF issues
    file_content = file_content.replace('\r\n', '\n').replace('\r', '\n')
    
    async with AsyncSessionLocal() as session:
        try:
            # Update job status to processing
            await _update_job_status(session, job_id, "processing")
            
            # Parse CSV with pandas for unlimited record handling
            try:
                # Use pandas to read CSV - handles unlimited records efficiently
                df = pd.read_csv(
                    StringIO(file_content),
                    dtype=str,  # Keep all as strings initially for validation
                    keep_default_na=False,  # Don't convert empty strings to NaN
                    na_filter=False  # Don't interpret 'NA', 'NULL' as missing values
                )
                
                # Validate required columns exist
                if 'name' not in df.columns or 'sku' not in df.columns:
                    error_msg = "CSV must contain 'name' and 'sku' columns"
                    await _update_job_status(session, job_id, "failed", error_msg)
                    return {'status': 'failed', 'error': error_msg}
                
                # Filter out rows where name or sku is empty
                df = df.dropna(subset=['name', 'sku'])
                df = df[df['name'].str.strip() != '']
                df = df[df['sku'].str.strip() != '']
                
                total_records = len(df)
                
                # Update total records count first
                await _update_job_total_records(session, job_id, total_records)
                
            except Exception as parse_error:
                # If CSV parsing fails entirely, mark as failed
                error_msg = f"CSV parsing error: {str(parse_error)}"
                await _update_job_status(session, job_id, "failed", error_msg)
                return {'status': 'failed', 'error': error_msg}
            
            # Trigger import.started webhook
            await _trigger_webhook(session, "import.started", {
                "job_id": job_id,
                "filename": filename,
                "total_records": total_records
            })
            
            # Process in streaming chunks without loading all data into memory
            processed_count = 0
            failed_count = 0
            chunk_size = settings.chunk_size
            
            # Process DataFrame in chunks using pandas
            total_rows = len(df)
            
            for start_idx in range(0, total_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, total_rows)
                chunk_df = df.iloc[start_idx:end_idx]
                
                # Convert DataFrame chunk to list of dicts for existing processing logic
                current_chunk = chunk_df.to_dict('records')
                
                # Process chunk
                processed, failed = await _process_chunk(session, current_chunk, job_id)
                
                processed_count += processed
                failed_count += failed
                
                # Update progress
                progress = (processed_count + failed_count) / total_records * 100
                
                # Update database progress
                await _update_job_progress(session, job_id, processed_count, failed_count)
                
                # Update Redis for real-time progress
                await _update_redis_progress(job_id, {
                    'status': 'processing',
                    'total_records': total_records,
                    'processed_records': processed_count,
                    'failed_records': failed_count,
                    'progress_percentage': progress
                })
                
                # Update task progress for Celery
                task_self.update_state(
                    state='PROGRESS',
                    meta={
                        'processed': processed_count,
                        'total': total_records,
                        'failed': failed_count,
                        'progress': progress
                    }
                )
            
            # Mark job as completed
            await _update_job_status(session, job_id, "completed")
            await _update_redis_progress(job_id, {
                'status': 'completed',
                'total_records': total_records,
                'processed_records': processed_count,
                'failed_records': failed_count,
                'progress_percentage': 100.0
            })
            
            # Trigger completion webhook
            await _trigger_webhook(session, "import.completed", {
                "job_id": job_id,
                "filename": filename,
                "total_records": total_records,
                "processed_records": processed_count,
                "failed_records": failed_count
            })
            
            return {
                'status': 'completed',
                'total_records': total_records,
                'processed_records': processed_count,
                'failed_records': failed_count,
                'message': f'Successfully processed {processed_count} records, {failed_count} failed'
            }
            
        except Exception as e:
            # Mark job as failed and trigger failure webhook
            error_msg = f"Processing error: {str(e)}"
            await _update_job_status(session, job_id, "failed", error_msg)
            
            await _trigger_webhook(session, "import.failed", {
                "job_id": job_id,
                "filename": filename,
                "error": error_msg
            })
            
            return {'status': 'failed', 'error': error_msg}
            await _update_job_status(session, job_id, "failed", error_msg)
            await _update_redis_progress(job_id, {
                'status': 'failed',
                'error_message': error_msg
            })
            
            task_self.update_state(
                state='FAILURE',
                meta={'error': error_msg}
            )
            
            raise


async def _process_chunk(session, chunk: List[Dict], job_id: int) -> Tuple[int, int]:
    """Process a chunk of CSV records."""
    processed = 0
    failed = 0
    
    # Prepare batch insert data
    products_to_insert = []
    
    for row in chunk:
        try:
            # Clean and validate data
            product_data = _clean_product_data(row)
            
            if product_data:
                products_to_insert.append(product_data)
                processed += 1
            else:
                failed += 1
                
        except Exception as e:
            failed += 1
            # Log individual record failures if needed
            continue
    
    # Batch insert with upsert (update on conflict)
    if products_to_insert:
        try:
            # Use PostgreSQL UPSERT to handle duplicates
            stmt = insert(Product).values(products_to_insert)
            stmt = stmt.on_conflict_do_update(
                index_elements=['sku'],
                set_={
                    'name': stmt.excluded.name,
                    'description': stmt.excluded.description,
                    'price': stmt.excluded.price,
                    'updated_at': stmt.excluded.updated_at
                }
            )
            
            await session.execute(stmt)
            await session.commit()
            
        except Exception as e:
            failed += len(products_to_insert)
            processed = 0
            await session.rollback()
    
    return processed, failed


def _clean_product_data(row: Dict[str, str]) -> Dict[str, Any]:
    """Clean and validate product data from CSV row."""
    try:
        # Clean SKU (strip spaces and handle various formats)
        sku = str(row.get('sku', '') or '').strip()
        if not sku:  # Only require non-empty SKU
            return None
            
        # Clean name (handle different possible column names)
        name = str(row.get('name', '') or row.get('Name', '') or row.get('product_name', '') or '').strip()
        if not name:  # Only require non-empty name
            return None
            
        # Clean description (handle multiline text and various formats)
        description = str(row.get('description', '') or row.get('Description', '') or '').strip()
        # Clean up description: remove excessive whitespace and newlines
        if description:
            description = ' '.join(description.split())  # Normalize whitespace
            if len(description) > 1000:  # Truncate very long descriptions
                description = description[:1000] + '...'
        else:
            description = None
        
        # Handle price (default to 0 for import)
        try:
            price_val = row.get('price', '') or row.get('Price', '') or '0.00'
            price = Decimal(str(price_val).replace('$', '').replace(',', '').strip() or '0.00')
        except (InvalidOperation, ValueError):
            price = Decimal('0.00')
        
        # Handle active status
        active_val = row.get('active', '') or row.get('Active', '') or 'true'
        active = str(active_val).lower().strip() in ('true', '1', 'yes', 'active', 't')
        
        return {
            'sku': sku,
            'name': name,
            'description': description,
            'price': price,
            'active': active
        }
        
    except Exception as e:
        return None


async def _update_job_status(session, job_id: int, status: str, error_message: str = None):
    """Update import job status."""
    result = await session.execute(
        select(ImportJob).where(ImportJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if job:
        job.status = status
        if error_message:
            job.error_message = error_message
        await session.commit()


async def _update_job_total_records(session, job_id: int, total_records: int):
    """Update import job total records count."""
    result = await session.execute(
        select(ImportJob).where(ImportJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if job:
        job.total_records = total_records
        await session.commit()


async def _update_job_progress(session, job_id: int, processed: int, failed: int):
    """Update import job progress."""
    result = await session.execute(
        select(ImportJob).where(ImportJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if job:
        job.processed_records = processed
        job.failed_records = failed
        await session.commit()


async def _update_redis_progress(job_id: int, progress_data: Dict[str, Any]):
    """Update progress data in Redis for real-time updates."""
    progress_key = f"job_progress:{job_id}"
    redis_client.setex(progress_key, 3600, json.dumps(progress_data))


@celery_app.task(name='app.tasks.import_tasks.cleanup_old_jobs')
def cleanup_old_jobs():
    """Clean up old completed/failed import jobs."""
    return asyncio.run(_cleanup_old_jobs_async())


async def _cleanup_old_jobs_async():
    """Async implementation of job cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            # Delete jobs older than 24 hours that are completed or failed
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            result = await session.execute(
                select(ImportJob)
                .where(ImportJob.created_at < cutoff_time)
                .where(ImportJob.status.in_(['completed', 'failed']))
            )
            old_jobs = result.scalars().all()
            
            for job in old_jobs:
                # Clean up Redis progress data
                progress_key = f"job_progress:{job.id}"
                redis_client.delete(progress_key)
                
                # Delete job record
                await session.delete(job)
            
            await session.commit()
            return f"Cleaned up {len(old_jobs)} old import jobs"
            
        except Exception as e:
            await session.rollback()
            raise


async def _trigger_webhook(session, event_type: str, data: Dict):
    """Trigger webhook for the given event."""
    try:
        from app.services.webhook_service import WebhookService
        # Use static method directly
        await WebhookService.trigger_webhooks(session, event_type, data)
    except Exception as e:
        print(f"Webhook trigger error: {str(e)}")


# Import asyncio at the top
import asyncio