"""
PostgreSQL Client for Railway Deployment

This module provides PostgreSQL database connectivity for Railway hosting.
"""

import os
import asyncio
from typing import Optional
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class PostgreSQLClient:
    """
    PostgreSQL client for Railway deployment
    """
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = None
        self.session_factory = None
        
    def _get_database_url(self) -> str:
        """Get database URL from Railway environment variables"""
        # Railway provides DATABASE_URL automatically
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            # Fallback for local development
            host = os.getenv('PGHOST', 'localhost')
            port = os.getenv('PGPORT', '5432')
            user = os.getenv('PGUSER', 'postgres')
            password = os.getenv('PGPASSWORD', 'password')
            database = os.getenv('PGDATABASE', 'hobbes')
            database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
        
        # Convert postgres:// to postgresql+asyncpg:// if needed
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        return database_url
    
    async def initialize(self):
        """Initialize the database connection"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=300
            )
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("PostgreSQL client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL client: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get a database session"""
        if not self.session_factory:
            await self.initialize()
        
        return self.session_factory()
    
    async def close(self):
        """Close the database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL client closed")

# Global instance
postgresql_client = PostgreSQLClient()

async def get_db_session():
    """Dependency for getting database session"""
    async with postgresql_client.get_session() as session:
        try:
            yield session
        finally:
            await session.close() 