"""
Webhook API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.db.database import get_db
from app.services.webhook_service import WebhookService
from app.models.schemas import (
    WebhookResponse, WebhookCreate, WebhookUpdate, 
    WebhookTestResponse, MessageResponse
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new webhook."""
    try:
        webhook = await WebhookService.create_webhook(db, webhook_data)
        
        # Convert the webhook to response format
        response = WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            event_types=WebhookService.parse_event_types(webhook.event_types),
            active=webhook.active,
            secret=webhook.secret,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at
        )
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[WebhookResponse])
async def get_webhooks(
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get webhooks with optional filtering."""
    webhooks = await WebhookService.get_webhooks(db, active_only, limit, offset)
    
    # Convert to response format
    response_webhooks = []
    for webhook in webhooks:
        response_webhooks.append(WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            event_types=WebhookService.parse_event_types(webhook.event_types),
            active=webhook.active,
            secret=webhook.secret,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at
        ))
    
    return response_webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a webhook by ID."""
    webhook = await WebhookService.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        event_types=WebhookService.parse_event_types(webhook.event_types),
        active=webhook.active,
        secret=webhook.secret,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at
    )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a webhook."""
    webhook = await WebhookService.update_webhook(db, webhook_id, webhook_data)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        event_types=WebhookService.parse_event_types(webhook.event_types),
        active=webhook.active,
        secret=webhook.secret,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at
    )


@router.delete("/{webhook_id}", response_model=MessageResponse)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a webhook."""
    success = await WebhookService.delete_webhook(db, webhook_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    return MessageResponse(message="Webhook deleted successfully")


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: int,
    test_payload: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Test a webhook endpoint."""
    webhook = await WebhookService.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    result = await WebhookService.test_webhook(webhook.url, test_payload)
    return result


@router.post("/test-url", response_model=WebhookTestResponse)
async def test_webhook_url(
    webhook_url: str,
    test_payload: Dict[str, Any] = None
):
    """Test a webhook URL without creating a webhook."""
    result = await WebhookService.test_webhook(webhook_url, test_payload)
    return result