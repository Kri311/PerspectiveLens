import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://perslens:supersecretpassword@localhost:5432/perslens")

async def update_sources():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await session.execute(text("UPDATE sources SET orientation = 'DRAVIDIAN' WHERE name ILIKE '%sun%' OR name ILIKE '%kalaignar%' OR name ILIKE '%murasoli%';"))
        await session.execute(text("UPDATE sources SET orientation = 'AIADMK' WHERE name ILIKE '%jaya%' OR name ILIKE '%namadhu amma%';"))
        await session.execute(text("UPDATE sources SET orientation = 'CONSERVATIVE' WHERE name ILIKE '%dinamalar%' OR name ILIKE '%janam%' OR name ILIKE '%thamarai%';"))
        await session.execute(text("UPDATE sources SET orientation = 'NEUTRAL' WHERE name ILIKE '%thanthi%' OR name ILIKE '%polimer%' OR name ILIKE '%puthiya%' OR name ILIKE '%hindu%' OR name ILIKE '%news18%' OR name ILIKE '%zee%';"))
        await session.commit()
        print("Updated existing sources with logical default orientations.")

if __name__ == "__main__":
    asyncio.run(update_sources())
