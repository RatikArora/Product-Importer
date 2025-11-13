"""
Product API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.services.product_service import ProductService
from app.models.schemas import (
    ProductResponse, ProductCreate, ProductUpdate, ProductFilter,
    PaginatedResponse, MessageResponse, BulkDeleteResponse
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new product."""
    try:
        # Check if SKU already exists
        existing_product = await ProductService.get_product_by_sku(db, product_data.sku)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )
        
        product = await ProductService.create_product(db, product_data)
        return product
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=PaginatedResponse)
async def get_products(
    search: str = None,
    sku: str = None,
    active: bool = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get products with filtering and pagination."""
    filters = ProductFilter(
        search=search,
        sku=sku,
        active=active,
        limit=min(limit, 100),  # Cap at 100
        offset=offset
    )
    
    products, total = await ProductService.get_products(db, filters)
    
    return PaginatedResponse(
        items=products,
        total=total,
        limit=filters.limit,
        offset=filters.offset,
        has_next=offset + limit < total,
        has_prev=offset > 0
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a product by ID."""
    product = await ProductService.get_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a product."""
    product = await ProductService.update_product(db, product_id, product_data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a product."""
    success = await ProductService.delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return MessageResponse(message="Product deleted successfully")


@router.delete("/", response_model=BulkDeleteResponse)
async def bulk_delete_products(db: AsyncSession = Depends(get_db)):
    """Delete all products."""
    deleted_count = await ProductService.bulk_delete_products(db)
    return BulkDeleteResponse(
        deleted_count=deleted_count,
        message=f"Successfully deleted {deleted_count} products"
    )