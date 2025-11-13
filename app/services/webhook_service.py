"""
Webhook service for managing webhook operations.
"""
import json
import asyncio
import httpx
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Webhook
from app.models.schemas import WebhookCreate, WebhookUpdate, WebhookTestResponse


class WebhookService:
    """Service class for webhook operations."""
    
    @staticmethod
    async def create_webhook(db: AsyncSession, webhook_data: WebhookCreate) -> Webhook:
        """Create a new webhook."""
        # Convert event_types list to JSON string for storage
        webhook_dict = webhook_data.model_dump()
        webhook_dict['event_types'] = json.dumps(webhook_data.event_types)
        webhook_dict['url'] = str(webhook_data.url)  # Convert HttpUrl to string
        
        webhook = Webhook(**webhook_dict)
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        return webhook
    
    @staticmethod
    async def get_webhook(db: AsyncSession, webhook_id: int) -> Optional[Webhook]:
        """Get webhook by ID."""
        result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_webhooks(
        db: AsyncSession,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Webhook]:
        """Get webhooks with optional filtering."""
        query = select(Webhook).order_by(Webhook.created_at.desc())
        
        if active_only:
            query = query.where(Webhook.active == True)
        
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_webhook(
        db: AsyncSession,
        webhook_id: int,
        webhook_data: WebhookUpdate
    ) -> Optional[Webhook]:
        """Update an existing webhook."""
        result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            return None
        
        update_data = webhook_data.model_dump(exclude_unset=True)
        
        # Handle event_types conversion
        if 'event_types' in update_data:
            update_data['event_types'] = json.dumps(update_data['event_types'])
        
        # Handle URL conversion
        if 'url' in update_data:
            update_data['url'] = str(update_data['url'])
        
        for field, value in update_data.items():
            setattr(webhook, field, value)
        
        await db.commit()
        await db.refresh(webhook)
        return webhook
    
    @staticmethod
    async def delete_webhook(db: AsyncSession, webhook_id: int) -> bool:
        """Delete a webhook by ID."""
        result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            return False
        
        await db.delete(webhook)
        await db.commit()
        return True
    
    @staticmethod
    async def test_webhook(webhook_url: str, test_payload: Dict[str, Any] = None) -> WebhookTestResponse:
        """Test a webhook endpoint."""
        if test_payload is None:
            test_payload = {
                "event": "test",
                "message": "This is a test webhook call",
                "timestamp": "2024-11-13T10:00:00Z"
            }
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=test_payload,
                    headers={"Content-Type": "application/json"}
                )
            
            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000
            
            return WebhookTestResponse(
                success=response.status_code < 400,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
        except asyncio.TimeoutError:
            return WebhookTestResponse(
                success=False,
                error="Request timeout (10 seconds)"
            )
        except Exception as e:
            return WebhookTestResponse(
                success=False,
                error=str(e)
            )
    
    @staticmethod
    def parse_event_types(event_types_json: str) -> List[str]:
        """Parse event types from JSON string."""
        try:
            return json.loads(event_types_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @staticmethod
    async def trigger_webhooks(
        db: AsyncSession,
        event_type: str,
        payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Trigger all active webhooks for a specific event type."""
        # Get all active webhooks
        result = await db.execute(
            select(Webhook).where(Webhook.active == True)
        )
        webhooks = result.scalars().all()
        
        # Filter webhooks that subscribe to this event type
        triggered_webhooks = []
        
        for webhook in webhooks:
            event_types = WebhookService.parse_event_types(webhook.event_types)
            
            if event_type in event_types or "all" in event_types:
                webhook_payload = {
                    "event": event_type,
                    "webhook_id": webhook.id,
                    "timestamp": payload.get("timestamp", ""),
                    "data": payload
                }
                
                # Trigger webhook asynchronously (fire and forget)
                asyncio.create_task(
                    WebhookService._send_webhook(webhook.url, webhook_payload, webhook.secret)
                )
                
                triggered_webhooks.append({
                    "webhook_id": webhook.id,
                    "webhook_name": webhook.name,
                    "url": webhook.url
                })
        
        return triggered_webhooks
    
    @staticmethod
    async def _send_webhook(url: str, payload: Dict[str, Any], secret: Optional[str] = None):
        """Send webhook payload to endpoint."""
        try:
            headers = {"Content-Type": "application/json"}
            
            # Add signature header if secret is provided
            if secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(url, json=payload, headers=headers)
                
        except Exception as e:
            # Log webhook delivery failure
            print(f"Webhook delivery failed for {url}: {e}")
            # In production, you'd want to implement retry logic and proper logging