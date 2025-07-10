"""
Database Initialization for Railway PostgreSQL

This script creates all necessary tables for the Hobbes app.
"""

import asyncio
import logging
from infrastructure.postgresql_client import postgresql_client, Base
from database.models import User, Project, Note, ProjectNote, ActionItem, AIFileRecord, AIConfiguration

logger = logging.getLogger(__name__)

async def create_tables():
    """
    Create all database tables for Railway deployment
    """
    try:
        # Initialize the PostgreSQL client
        await postgresql_client.initialize()
        
        # Create all tables
        async with postgresql_client.engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ All database tables created successfully")
            
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise
    finally:
        await postgresql_client.close()

async def drop_tables():
    """
    Drop all database tables (for development/testing)
    """
    try:
        await postgresql_client.initialize()
        
        async with postgresql_client.engine.begin() as conn:
            logger.info("Dropping all database tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("✅ All database tables dropped successfully")
            
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise
    finally:
        await postgresql_client.close()

if __name__ == "__main__":
    # Run table creation
    asyncio.run(create_tables()) 