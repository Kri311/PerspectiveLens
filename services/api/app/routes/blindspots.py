from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.dependencies.database import get_db
from .events import translate_text

router = APIRouter(prefix="/blindspots", tags=["blindspots"])

@router.get("/")
async def get_global_blindspots(lang: str = Query("en", description="Language code (en or ta)"), db: AsyncSession = Depends(get_db)):
    """
    Returns a global feed of active blindspots across all events, 
    ranked by severity score.
    """
    query = text("""
        SELECT 
            b.id,
            b.event_id,
            e.representative_title as event_title,
            b.source_group,
            b.blindspot_type,
            b.score,
            b.evidence,
            b.created_at
        FROM blindspot_candidates b
        JOIN events e ON e.id = b.event_id
        WHERE b.status = 'candidate'
        ORDER BY b.score DESC
        LIMIT 50
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    blindspots = []
    for row in rows:
        title_translated = await translate_text(row.event_title, lang) if row.event_title else None
        blindspots.append({
            "id": str(row.id),
            "event_id": str(row.event_id),
            "event_title": title_translated,
            "source_group": row.source_group,
            "blindspot_type": row.blindspot_type,
            "score": row.score,
            "evidence": row.evidence,
            "created_at": row.created_at
        })
        
    return {"blindspots": blindspots}
