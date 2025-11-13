"""
Product service for business logic operations.
"""
import json
import redis
from typing import List, Optional, Tuple
from decimal import Decimal
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Product, ImportJob
from app.models.schemas import ProductCreate, ProductUpdate, ProductFilter
from app.core.config import settings

redis_client = redis.Redis.from_url(settings.effective_redis_url)


class ProductService:
    """Service class for product operations."""
    
    @staticmethod
    async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
        """Create a new product."""
        # Convert SKU to lowercase for case-insensitive uniqueness
        product_dict = product_data.model_dump()
        product_dict['sku'] = product_dict['sku'].lower().strip()
        
        product = Product(**product_dict)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product
    
    @staticmethod
    async def get_product(db: AsyncSession, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_product_by_sku(db: AsyncSession, sku: str) -> Optional[Product]:
        """Get product by SKU (case-insensitive)."""
        sku_lower = sku.lower().strip()
        result = await db.execute(select(Product).where(Product.sku == sku_lower))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_products(
        db: AsyncSession,
        filters: ProductFilter
    ) -> Tuple[List[Product], int]:
        """Get products with filtering and pagination."""
        
        # Base query
        query = select(Product)
        count_query = select(func.count(Product.id))
        
        # Apply filters
        conditions = []
        
        if filters.search:
            search_term = f"%{filters.search.lower()}%"
            conditions.append(
                or_(
                    func.lower(Product.name).contains(search_term),
                    func.lower(Product.sku).contains(search_term),
                    func.lower(Product.description).contains(search_term)
                )
            )
        
        if filters.sku:
            conditions.append(Product.sku == filters.sku.lower().strip())
        
        if filters.active is not None:
            conditions.append(Product.active == filters.active)
        
        # Apply conditions to both queries
        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        
        # Get total count
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination and ordering
        query = (
            query
            .order_by(Product.created_at.desc())
            .offset(filters.offset)
            .limit(filters.limit)
        )
        
        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()
        
        return list(products), total
    
    @staticmethod
    async def update_product(
        db: AsyncSession,
        product_id: int,
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """Update an existing product."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        update_data = product_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(product, field, value)
        
        await db.commit()
        await db.refresh(product)
        return product
    
    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int) -> bool:
        """Delete a product by ID."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            return False
        
        await db.delete(product)
        await db.commit()
        return True
    
    @staticmethod
    async def bulk_delete_products(db: AsyncSession) -> int:
        """Delete all products."""
        result = await db.execute(delete(Product))
        deleted_count = result.rowcount
        await db.commit()
        return deleted_count
    
    @staticmethod
    async def get_products_count(db: AsyncSession) -> int:
        """Get total number of products."""
        result = await db.execute(select(func.count(Product.id)))
        return result.scalar()


class ImportJobService:
    """Service class for import job operations."""
    
    @staticmethod
    async def create_import_job(db: AsyncSession, filename: str) -> ImportJob:
        """Create a new import job."""
        job = ImportJob(filename=filename, status="pending")
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    
    @staticmethod
    async def get_import_job(db: AsyncSession, job_id: int) -> Optional[ImportJob]:
        """Get import job by ID."""
        result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_job_progress(job_id: int) -> dict:
        """Get job progress from Redis."""
        progress_key = f"job_progress:{job_id}"
        progress_data = redis_client.get(progress_key)
        
        if progress_data:
            return json.loads(progress_data)
        
        # Fallback to database if Redis data not available
        return {
            'status': 'unknown',
            'total_records': 0,
            'processed_records': 0,
            'failed_records': 0,
            'progress_percentage': 0.0
        }
    
    @staticmethod
    async def get_recent_jobs(db: AsyncSession, limit: int = 10) -> List[ImportJob]:
        """Get recent import jobs."""
        result = await db.execute(
            select(ImportJob)
            .order_by(ImportJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())