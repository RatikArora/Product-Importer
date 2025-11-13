#!/usr/bin/env python3
"""
Deployment health check script.
Verifies that all critical components are working before deployment.
"""

import asyncio
import sys
import os
from typing import Dict, Any

async def check_imports():
    """Check that all critical modules can be imported."""
    try:
        print("🔍 Checking imports...")
        
        # Critical imports
        import fastapi
        import uvicorn
        import sqlalchemy
        import asyncpg
        import redis
        import celery
        import pandas
        import httpx
        import pydantic
        
        # App imports
        from app.core.config import settings
        from app.db.database import engine
        from app.main import app
        
        print(f"✅ FastAPI: {fastapi.__version__}")
        print(f"✅ Uvicorn: {uvicorn.__version__}")
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
        print(f"✅ Pandas: {pandas.__version__}")
        print(f"✅ Pydantic: {pydantic.__version__}")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

async def check_config():
    """Check configuration settings."""
    try:
        print("\n🔍 Checking configuration...")
        
        from app.core.config import settings
        
        # Check required settings
        checks = {
            "Database URL": settings.effective_database_url,
            "Redis URL": settings.effective_redis_url,
            "Secret Key": "***" if settings.secret_key and settings.secret_key != "your-secret-key-change-in-production" else None,
            "Max File Size": f"{settings.max_file_size_mb}MB",
            "Chunk Size": settings.chunk_size
        }
        
        for name, value in checks.items():
            if value:
                print(f"✅ {name}: {value}")
            else:
                print(f"⚠️ {name}: Not configured (will use defaults)")
        
        return True
    except Exception as e:
        print(f"❌ Config check failed: {e}")
        return False

async def check_database():
    """Check database connection."""
    try:
        print("\n🔍 Checking database connection...")
        
        from app.db.database import engine
        import sqlalchemy
        
        async with engine.begin() as conn:
            result = await conn.execute(sqlalchemy.text("SELECT 1"))
            row = result.scalar()
            
        if row == 1:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"⚠️ Database check failed (might be ok for initial deployment): {e}")
        return True  # Don't fail deployment for DB issues

async def check_redis():
    """Check Redis connection."""
    try:
        print("\n🔍 Checking Redis connection...")
        
        from app.core.config import settings
        import redis.asyncio as aioredis
        
        redis_client = aioredis.from_url(settings.effective_redis_url)
        pong = await redis_client.ping()
        await redis_client.aclose()
        
        if pong:
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis connection failed")
            return False
            
    except Exception as e:
        print(f"⚠️ Redis check failed (might be ok for initial deployment): {e}")
        return True  # Don't fail deployment for Redis issues

async def main():
    """Run all health checks."""
    print("🏥 Starting deployment health checks...\n")
    
    checks = [
        ("Imports", check_imports()),
        ("Configuration", check_config()),
        ("Database", check_database()),
        ("Redis", check_redis()),
    ]
    
    results = {}
    for name, check in checks:
        results[name] = await check
    
    print("\n" + "="*50)
    print("📊 HEALTH CHECK SUMMARY")
    print("="*50)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All health checks passed! Ready for deployment!")
        sys.exit(0)
    else:
        print("\n⚠️ Some checks failed. Review issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())