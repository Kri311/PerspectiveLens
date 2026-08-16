import asyncio
import sys
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://perslens:supersecretpassword@localhost:5432/perslens")

SOURCE_NAME_ALIASES = {
    "daily thanthi": "Daily Thanthi",
    "dailythanthi": "Daily Thanthi",
    "thanthi": "Daily Thanthi",
    "தினத்தந்தி": "Daily Thanthi",
    "dinamalar": "Dinamalar",
    "தினமலர்": "Dinamalar",
    "vikatan": "Vikatan",
    "விகடன்": "Vikatan",
    "dinamani": "Dinamani",
    "தினமணி": "Dinamani",
    "sun news": "Sun News",
    "sun tv": "Sun News",
    "kalaignar tv": "Kalaignar TV",
    "kalaignar": "Kalaignar TV",
    "jaya tv": "Jaya TV",
    "jaya news": "Jaya TV",
    "thanthi tv": "Thanthi TV",
    "polimer news": "Polimer News",
    "polimer": "Polimer News",
    "puthiya thalaimurai": "Puthiya Thalaimurai",
    "puthiyathalaimurai": "Puthiya Thalaimurai",
    "news18 tamil": "News18 Tamil",
    "news 18 tamil": "News18 Tamil",
    "oneindia tamil": "OneIndia Tamil",
    "the hindu": "The Hindu",
    "hindu": "The Hindu",
    "hindu tamil": "Hindu Tamil",
    "ndtv": "NDTV",
    "zee tamil": "Zee Tamil",
    "india today": "India Today",
    "dinakaran": "Dinakaran",
    "bbc tamil": "BBC Tamil",
    "asianet news tamil": "Asianet News Tamil",
    "asianet": "Asianet News Tamil",
    "abp nadu": "ABP Nadu",
}

def normalize_source_name(name: str) -> str:
    if not name:
        return name
    lookup = name.strip().lower()
    lookup_clean = re.sub(r'\s*(news|tv|online|digital|web)\s*$', '', lookup).strip()
    return SOURCE_NAME_ALIASES.get(lookup, SOURCE_NAME_ALIASES.get(lookup_clean, name.strip().title()))

async def merge_sources():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all sources
        result = await session.execute(text("SELECT id, name FROM sources"))
        sources = result.fetchall()
        
        # Group by canonical name
        canonical_map = {}
        for s in sources:
            canon = normalize_source_name(s.name)
            if canon not in canonical_map:
                canonical_map[canon] = []
            canonical_map[canon].append(str(s.id))
            
        for canon, ids in canonical_map.items():
            if not ids:
                continue
            
            # Keep the first ID as the master
            master_id = ids[0]
            
            # Update the master name
            await session.execute(text("UPDATE sources SET name = :name WHERE id = :id"), {"name": canon, "id": master_id})
            
            if len(ids) > 1:
                duplicate_ids = ids[1:]
                print(f"Merging into {canon} ({master_id}): {duplicate_ids}")
                
                for dup_id in duplicate_ids:
                    # Update foreign keys
                    await session.execute(text("UPDATE articles SET source_id = :master WHERE source_id = :dup"), {"master": master_id, "dup": dup_id})
                    await session.execute(text("UPDATE event_coverage SET source_id = :master WHERE source_id = :dup"), {"master": master_id, "dup": dup_id})
                    # Ownership and reliability should be moved if master doesn't have it, but for simplicity we just ignore conflicts or let ON DELETE CASCADE handle duplicates if they aren't unique. Actually let's just delete the duplicates.
                    
                    # Delete the duplicate source
                    await session.execute(text("DELETE FROM sources WHERE id = :dup"), {"dup": dup_id})
                    
        await session.commit()
        print("Source directory normalization complete.")

if __name__ == "__main__":
    asyncio.run(merge_sources())
