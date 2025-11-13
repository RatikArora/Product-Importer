"""
Pydantic schemas for request and response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# Product Schemas
class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU (case-insensitive unique)")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[Decimal] = Field(default=0.00, ge=0, description="Product price")
    active: bool = Field(default=True, description="Whether the product is active")


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    price: Optional[Decimal] = Field(None, ge=0)
    active: Optional[bool] = Field(None)


class ProductResponse(ProductBase):
    """Schema for product response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class ProductFilter(BaseModel):
    """Schema for filtering products."""
    search: Optional[str] = Field(None, description="Search in name, SKU, or description")
    sku: Optional[str] = Field(None, description="Filter by SKU")
    active: Optional[bool] = Field(None, description="Filter by active status")
    limit: int = Field(default=20, ge=1, le=100, description="Number of records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


# Webhook Schemas
class WebhookBase(BaseModel):
    """Base webhook schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    url: HttpUrl = Field(..., description="Webhook URL")
    event_types: List[str] = Field(..., description="List of event types to subscribe to")
    active: bool = Field(default=True, description="Whether the webhook is active")
    secret: Optional[str] = Field(None, max_length=255, description="Optional webhook secret")


class WebhookCreate(WebhookBase):
    """Schema for creating a new webhook."""
    pass


class WebhookUpdate(BaseModel):
    """Schema for updating an existing webhook."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = Field(None)
    event_types: Optional[List[str]] = Field(None)
    active: Optional[bool] = Field(None)
    secret: Optional[str] = Field(None, max_length=255)


class WebhookResponse(BaseModel):
    """Schema for webhook response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    url: str
    event_types: List[str]
    active: bool
    secret: Optional[str]
    created_at: datetime
    updated_at: datetime


class WebhookTestResponse(BaseModel):
    """Schema for webhook test response."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


# Import Job Schemas
class ImportJobResponse(BaseModel):
    """Schema for import job response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    total_records: int
    processed_records: int
    failed_records: int
    status: str
    error_message: Optional[str]
    progress_percentage: float
    created_at: datetime
    updated_at: datetime


# Upload Schemas
class UploadResponse(BaseModel):
    """Schema for file upload response."""
    job_id: int
    message: str
    total_records: int


class ProgressResponse(BaseModel):
    """Schema for progress response."""
    job_id: int
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    progress_percentage: float
    error_message: Optional[str] = None


# Generic Response Schemas
class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str


class BulkDeleteResponse(BaseModel):
    """Schema for bulk delete response."""
    deleted_count: int
    message: str


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    items: List[ProductResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool


# Health Check Schema
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    redis: str
    celery: str
    timestamp: datetime