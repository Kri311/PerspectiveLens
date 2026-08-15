from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.dependencies.database import get_db
import uuid

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/")
async def get_events(db: AsyncSession = Depends(get_db)):
    """Returns a list of all events."""
    query = text("""
        SELECT e.id, e.representative_title, e.summary, e.first_seen, e.status, 
               e.image_url, e.tags,
               COUNT(a.id) as article_count, COUNT(DISTINCT a.source_id) as source_count
        FROM events e
        LEFT JOIN articles a ON a.event_id = e.id
        GROUP BY e.id
        ORDER BY e.first_seen DESC
        LIMIT 50
    """)
    result = await db.execute(query)
    rows = result.fetchall()
    
    events = []
    for row in rows:
        # Fallback image if null
        img = row.image_url if hasattr(row, 'image_url') and row.image_url else "https://images.unsplash.com/photo-1572949645841-094f3a9c4c94?q=80&w=800&auto=format&fit=crop"
        
        # Determine some mock tags based on title if tags is null
        tags = row.tags if hasattr(row, 'tags') and row.tags else []
        title_lower = (row.representative_title or "").lower()
        if not tags:
            if any(word in title_lower for word in ["முதல்வர்", "அரசு", "அரசியல்", "தேர்தல்", "திமுக", "அதிமுக", "பாஜக", "காங்கிரஸ்"]):
                tags = ["Politics", "Government"]
            elif any(word in title_lower for word in ["மழை", "வெள்ளம்", "வானிலை"]):
                tags = ["Weather", "Environment"]
            elif any(word in title_lower for word in ["சென்னை", "கோவை", "மதுரை", "திருச்சி"]):
                tags = ["Local News", "City"]
            elif any(word in title_lower for word in ["பள்ளி", "கல்லூரி", "கல்வி"]):
                tags = ["Education", "Society"]
            elif any(word in title_lower for word in ["காவல்துறை", "கைது", "நீதிமன்றம்"]):
                tags = ["Crime", "Law"]
            elif any(word in title_lower for word in ["கிரிக்கெட்", "விளையாட்டு"]):
                tags = ["Sports", "Entertainment"]
            else:
                tags = ["Tamil Nadu", "Breaking News"]
                
        events.append({
            "id": str(row.id),
            "title": row.representative_title,
            "summary": row.summary,
            "first_seen": row.first_seen,
            "status": row.status,
            "article_count": row.article_count,
            "source_count": row.source_count,
            "image_url": img,
            "tags": tags
        })
    return events

@router.get("/{event_id}")
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns the event metadata and the generated summary."""
    event_id_str = str(event_id)
    query = text("""
        SELECT id, representative_title, summary, first_seen, status
        FROM events
        WHERE id = :event_id
    """)
    result = await db.execute(query, {"event_id": event_id_str})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return {
        "id": str(row.id),
        "title": row.representative_title,
        "summary": row.summary,
        "first_seen": row.first_seen,
        "status": row.status
    }

@router.get("/{event_id}/matrix")
async def get_perspective_matrix(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns the Perspective Matrix for a specific event.
    Aggregates Sentiment and Framing data grouped by Source.
    """
    event_id_str = str(event_id)
    query = text("""
        SELECT 
            s.name as source_name,
            COUNT(a.id) as article_count,
            SUM(CASE WHEN aa.sentiment = 'POSITIVE' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN aa.sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_count,
            SUM(CASE WHEN aa.sentiment = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN aa.stance = 'SUPPORT' THEN 1 ELSE 0 END) as support_count,
            SUM(CASE WHEN aa.stance = 'OPPOSE' THEN 1 ELSE 0 END) as oppose_count,
            SUM(CASE WHEN aa.stance = 'NEUTRAL' THEN 1 ELSE 0 END) as stance_neutral_count,
            jsonb_agg(aa.frame_distribution) as frames
        FROM events e
        JOIN articles a ON a.event_id = e.id
        JOIN sources s ON a.source_id = s.id
        LEFT JOIN article_analysis aa ON aa.article_id = a.id
        WHERE e.id = :event_id
        GROUP BY s.name
    """)
    
    result = await db.execute(query, {"event_id": event_id_str})
    rows = result.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Event not found or no articles analyzed yet.")
        
    matrix = []
    for row in rows:
        # Calculate average frame distribution for this source
        aggregated_frames = {}
        total_frames_analyzed = 0
        
        for frame_dist in row.frames:
            if not frame_dist:
                continue
            for frame_name, score in frame_dist.items():
                aggregated_frames[frame_name] = aggregated_frames.get(frame_name, 0) + score
            total_frames_analyzed += 1
            
        if total_frames_analyzed > 0:
            for k in aggregated_frames.keys():
                aggregated_frames[k] = round((aggregated_frames[k] / total_frames_analyzed) * 100, 1)
                
        matrix.append({
            "source": row.source_name,
            "article_count": row.article_count,
            "sentiment": {
                "positive": row.positive_count,
                "negative": row.negative_count,
                "neutral": row.neutral_count
            },
            "stance": {
                "support": row.support_count,
                "oppose": row.oppose_count,
                "neutral": row.stance_neutral_count
            },
            "average_framing": aggregated_frames
        })
        
    return {"event_id": event_id_str, "matrix": matrix}

@router.get("/{event_id}/claims")
async def get_event_claims(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns all factual claims extracted for this event and any detected contradictions."""
    event_id_str = str(event_id)
    query = text("""
        SELECT c.id, c.claim_text, c.claim_type, a.url, s.name as source_name
        FROM claims c
        JOIN articles a ON a.id = c.article_id
        JOIN sources s ON s.id = a.source_id
        WHERE c.event_id = :event_id
    """)
    result = await db.execute(query, {"event_id": event_id_str})
    rows = result.fetchall()
    
    claims = []
    for row in rows:
        claims.append({
            "id": str(row.id),
            "text": row.claim_text,
            "type": row.claim_type,
            "source": row.source_name,
            "url": row.url
        })
    return {"event_id": event_id_str, "claims": claims}

@router.get("/{event_id}/blindspots")
async def get_event_blindspots(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Returns blindspots specifically for this event."""
    event_id_str = str(event_id)
    query = text("""
        SELECT id, source_group, blindspot_type, score, evidence
        FROM blindspot_candidates
        WHERE event_id = :event_id
        ORDER BY score DESC
    """)
    result = await db.execute(query, {"event_id": event_id_str})
    rows = result.fetchall()
    
    blindspots = []
    for row in rows:
        blindspots.append({
            "id": str(row.id),
            "source_group": row.source_group,
            "type": row.blindspot_type,
            "score": row.score,
            "evidence": row.evidence
        })
    return {"event_id": event_id_str, "blindspots": blindspots}
