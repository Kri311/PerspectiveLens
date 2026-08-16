from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.dependencies.database import get_db
from .events import normalize_source_name
import uuid

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/")
async def get_all_sources(db: AsyncSession = Depends(get_db)):
    """Returns a list of all configured sources with normalized names (duplicates grouped)."""
    query = text("""
        SELECT id, name, domain, language, orientation, orientation_confidence, orientation_evidence, last_reviewed
        FROM sources
        ORDER BY name ASC
    """)
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Group by normalized name to avoid duplicates like "daily thandhi" / "Daily Thandhi"
    seen_names = {}
    sources = []
    for row in rows:
        canonical = normalize_source_name(row.name)
        if canonical in seen_names:
            continue
        seen_names[canonical] = True
        sources.append({
            "id": str(row.id),
            "name": canonical,
            "domain": row.domain,
            "language": row.language,
            "orientation": row.orientation,
            "confidence": row.orientation_confidence,
            "evidence": row.orientation_evidence,
            "last_reviewed": row.last_reviewed
        })
    return {"sources": sources}

@router.get("/{source_id}")
async def get_source(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns basic details for a specific source."""
    source_id_str = str(source_id)
    query = text("""
        SELECT id, name, domain, language, orientation, orientation_confidence, orientation_evidence
        FROM sources
        WHERE id = :id
    """)
    result = await db.execute(query, {"id": source_id_str})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Source not found")
        
    return {
        "id": str(row.id),
        "name": row.name,
        "domain": row.domain,
        "language": row.language,
        "orientation": row.orientation,
        "confidence": row.orientation_confidence,
        "evidence": row.orientation_evidence
    }

@router.get("/{source_id}/profile")
async def get_source_profile(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Dynamically generates the historical editorial profile for a source.
    Instead of relying on a batch-updated table, we aggregate the latest article_analysis data on the fly.
    """
    source_id_str = str(source_id)
    # Verify source exists
    source_query = text("SELECT name, orientation FROM sources WHERE id = :id")
    result = await db.execute(source_query, {"id": source_id_str})
    source_row = result.fetchone()
    
    if not source_row:
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Aggregate sentiment distribution
    sentiment_query = text("""
        SELECT sentiment, COUNT(*) as count
        FROM article_analysis aa
        JOIN articles a ON a.id = aa.article_id
        WHERE a.source_id = :id
        GROUP BY sentiment
    """)
    sent_result = await db.execute(sentiment_query, {"id": source_id_str})
    
    # Aggregate framing distribution
    framing_query = text("""
        SELECT frame, COUNT(*) as count
        FROM (
            SELECT jsonb_object_keys(aa.frame_distribution) as frame
            FROM article_analysis aa
            JOIN articles a ON a.id = aa.article_id
            WHERE a.source_id = :id
        ) f
        GROUP BY frame
    """)
    frame_result = await db.execute(framing_query, {"id": source_id_str})
    
    # Total articles analyzed
    count_query = text("SELECT COUNT(*) FROM articles WHERE source_id = :id AND status = 'processed'")
    count_result = await db.execute(count_query, {"id": source_id_str})
    total_analyzed = count_result.scalar() or 0
    
    return {
        "source_id": source_id_str,
        "name": source_row.name,
        "orientation": source_row.orientation,
        "total_analyzed_articles": total_analyzed,
        "historical_sentiment_distribution": {row.sentiment: row.count for row in sent_result.fetchall()},
        "historical_frame_distribution": {row.frame: row.count for row in frame_result.fetchall()}
    }

@router.get("/{source_id}/transparency")
async def get_source_transparency(source_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns transparency metadata including ownership, political affiliations, and reliability.
    """
    source_id_str = str(source_id)
    query = text("""
        SELECT 
            s.name as source_name,
            o.name as company_name,
            o.parent_company,
            o.owner,
            o.political_or_affiliate_links,
            r.reliability_level,
            r.historical_notes,
            r.correction_history
        FROM sources s
        LEFT JOIN ownership_entities o ON o.source_id = s.id
        LEFT JOIN source_reliability r ON r.source_id = s.id
        WHERE s.id = :id
    """)
    
    result = await db.execute(query, {"id": source_id_str})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Source not found")
        
    return {
        "source_id": source_id_str,
        "source_name": row.source_name,
        "ownership": {
            "company_name": row.company_name,
            "parent_company": row.parent_company,
            "owner": row.owner,
            "political_affiliations": row.political_or_affiliate_links
        },
        "reliability": {
            "level": row.reliability_level,
            "notes": row.historical_notes,
            "correction_history": row.correction_history
        }
    }
