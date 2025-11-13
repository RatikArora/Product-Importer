"""
Upload API endpoints for file processing.
"""
import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.db.database import get_db
from app.services.product_service import ImportJobService
from app.tasks.celery_app import celery_app
from app.models.schemas import UploadResponse, ProgressResponse, ImportJobResponse
from app.core.config import settings

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a CSV file for processing."""
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Check file size
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if file.size and file.size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
        )
    
    try:
        # Create import job record
        job = await ImportJobService.create_import_job(db, file.filename)
        
        # Read file content and normalize line endings
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # Fix mixed line endings (CRLF + LF) that cause CSV parsing issues
        file_content = file_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Count valid records using pandas (same as processing)
        import pandas as pd
        from io import StringIO
        try:
            # Use pandas to read CSV - handles unlimited records efficiently
            df = pd.read_csv(
                StringIO(file_content),
                dtype=str,  # Keep all as strings initially for validation
                keep_default_na=False,  # Don't convert empty strings to NaN
                na_filter=False  # Don't interpret 'NA', 'NULL' as missing values
            )
            
            # Validate required columns exist and count valid rows
            if 'name' in df.columns and 'sku' in df.columns:
                # Filter out rows where name or sku is empty
                df = df.dropna(subset=['name', 'sku'])
                df = df[df['name'].str.strip() != '']
                df = df[df['sku'].str.strip() != '']
                total_records = len(df)
            else:
                total_records = 0
                    
        except Exception as e:
            print(f"CSV counting error: {e}")
            total_records = 0
        
        # Update job with total records count
        job.total_records = total_records
        await db.commit()
        
        # Save file to uploads directory
        os.makedirs(settings.upload_directory, exist_ok=True)
        file_path = os.path.join(settings.upload_directory, f"job_{job.id}_{file.filename}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Start async processing task
        task = celery_app.send_task(
            'app.tasks.import_tasks.process_csv_upload',
            args=[file_content, file.filename, job.id]
        )
        
        return UploadResponse(
            job_id=job.id,
            message=f"File upload successful. Processing started for {total_records} records.",
            total_records=total_records
        )
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/progress/{job_id}", response_model=ProgressResponse)
async def get_upload_progress(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get upload progress for a specific job."""
    
    # Check if job exists
    job = await ImportJobService.get_import_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found"
        )
    
    # Get progress from Redis/Database
    progress = await ImportJobService.get_job_progress(job_id)
    
    return ProgressResponse(
        job_id=job_id,
        status=progress.get('status', job.status),
        total_records=progress.get('total_records', job.total_records),
        processed_records=progress.get('processed_records', job.processed_records),
        failed_records=progress.get('failed_records', job.failed_records),
        progress_percentage=progress.get('progress_percentage', job.progress_percentage),
        error_message=progress.get('error_message', job.error_message)
    )


@router.get("/progress/{job_id}/stream")
async def stream_upload_progress(job_id: int, db: AsyncSession = Depends(get_db)):
    """Stream upload progress using Server-Sent Events."""
    
    # Check if job exists
    job = await ImportJobService.get_import_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found"
        )
    
    async def progress_generator() -> AsyncGenerator[str, None]:
        """Generate progress updates via SSE."""
        import json
        import asyncio
        
        while True:
            # Get current progress
            progress = await ImportJobService.get_job_progress(job_id)
            status_value = progress.get('status', 'unknown')
            
            # Format SSE message
            data = {
                "job_id": job_id,
                "status": status_value,
                "total_records": progress.get('total_records', 0),
                "processed_records": progress.get('processed_records', 0),
                "failed_records": progress.get('failed_records', 0),
                "progress_percentage": progress.get('progress_percentage', 0.0),
                "error_message": progress.get('error_message')
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            # Stop streaming if job is completed or failed
            if status_value in ['completed', 'failed']:
                break
            
            # Wait before next update
            await asyncio.sleep(2)
    
    return StreamingResponse(
        progress_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/jobs", response_model=list[ImportJobResponse])
async def get_import_jobs(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent import jobs."""
    jobs = await ImportJobService.get_recent_jobs(db, limit)
    return jobs


@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific import job details."""
    job = await ImportJobService.get_import_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found"
        )
    return job