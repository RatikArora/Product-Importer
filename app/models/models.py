"""
Database models for the Product Importer application.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, Numeric, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Product(Base):
    """Product model representing imported products."""
    
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True, default=0.00)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Create composite indexes for better query performance
    __table_args__ = (
        Index('idx_product_sku_lower', 'sku'),
        Index('idx_product_active_created', 'active', 'created_at'),
        Index('idx_product_name_active', 'name', 'active'),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', active={self.active})>"


class Webhook(Base):
    """Webhook model for managing webhook endpoints."""
    
    __tablename__ = "webhooks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    event_types: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of event types
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Index for active webhooks
    __table_args__ = (
        Index('idx_webhook_active', 'active'),
    )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}', active={self.active})>"


class ImportJob(Base):
    """Import job model to track CSV import progress."""
    
    __tablename__ = "import_jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_records: Mapped[int] = mapped_column(default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)  # pending, processing, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_import_job_status_created', 'status', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, filename='{self.filename}', status='{self.status}', progress={self.processed_records}/{self.total_records})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100