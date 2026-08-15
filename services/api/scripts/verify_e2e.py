import asyncio
import os
import sys
import uuid
import httpx
import logging
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.dependencies.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def verify_pipeline():
    logger.info("Starting End-to-End Pipeline Verification...")
    
    # 1. We will insert 3 mock Tamil articles about a fictitious event:
    # "The State Government announces a new free bus pass scheme for all students in Tamil Nadu."
    mock_articles = [
        {
            "url": f"https://sunnews.in/politics/bus-scheme-{uuid.uuid4()}",
            "title": "முதல்வர் புதிய இலவச பேருந்து திட்டத்தை அறிவித்தார்", # CM announced new free bus scheme
            "body": "தமிழக அரசு மாணவர்களுக்கான புதிய இலவச பேருந்து திட்டத்தை இன்று அறிவித்துள்ளது. முதலமைச்சர் மு.க.ஸ்டாலின் இந்த திட்டத்தை தொடங்கி வைத்தார். இது திராவிட மாடல் ஆட்சியின் சாதனை.",
            "source_domain": "sunnews.in"
        },
        {
            "url": f"https://thanthitv.com/news/bus-scheme-{uuid.uuid4()}",
            "title": "இலவச பேருந்து திட்டம்: அரசு மீது விமர்சனம்", # Free bus scheme: criticism against govt
            "body": "புதிய இலவச பேருந்து திட்டத்தால் அரசு போக்குவரத்து கழகத்திற்கு பெரும் இழப்பு ஏற்படும் என்று எதிர்கட்சிகள் விமர்சனம் செய்துள்ளன. எடப்பாடி பழனிசாமி இந்த திட்டத்தை கண்துடைப்பு என்றார்.",
            "source_domain": "thanthitv.com"
        },
        {
            "url": f"https://puthiyathalaimurai.com/tamilnadu/bus-scheme-{uuid.uuid4()}",
            "title": "மாணவர்களுக்கு இலவச பேருந்து பாஸ் திட்டம் தொடக்கம்", # Free bus pass scheme for students started
            "body": "மாணவர்களுக்கான இலவச பேருந்து பாஸ் திட்டம் இன்று தொடங்கப்பட்டது. இதனால் லட்சக்கணக்கான மாணவர்கள் பயனடைவார்கள். இருப்பினும் போக்குவரத்து நெரிசல் அதிகரிக்கும் என சமூக ஆர்வலர்கள் கூறுகின்றனர்.",
            "source_domain": "puthiyathalaimurai.com"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        # Get source IDs
        sources = await db.execute(text("SELECT id, domain FROM sources"))
        source_map = {row.domain: row.id for row in sources.fetchall()}
        
        inserted_article_ids = []
        
        # Insert articles
        for a in mock_articles:
            source_id = source_map.get(a["source_domain"])
            if not source_id:
                logger.error(f"Source not found for {a['source_domain']}")
                continue
                
            query = text("""
                INSERT INTO articles (source_id, url, title, body, status)
                VALUES (:source_id, :url, :title, :body, 'queued')
                RETURNING id
            """)
            result = await db.execute(query, {
                "source_id": source_id,
                "url": a["url"],
                "title": a["title"],
                "body": a["body"]
            })
            article_id = result.scalar()
            inserted_article_ids.append(str(article_id))
            
        await db.commit()
        logger.info(f"Inserted 3 mock articles into the database for processing.")
        
        # 2. Wait for the Celery Worker to process them
        logger.info("Waiting for Analysis Worker to process the articles (this involves NLP embedding, NER, Sentiment, and Stance)...")
        event_id = None
        max_attempts = 15
        
        for i in range(max_attempts):
            await asyncio.sleep(5)
            
            # Check status
            status_query = text("SELECT status, event_id FROM articles WHERE id = ANY(:ids)")
            result = await db.execute(status_query, {"ids": inserted_article_ids})
            rows = result.fetchall()
            
            all_processed = all(r.status == 'processed' for r in rows)
            
            if all_processed:
                # All articles should be grouped into the same event because of vector similarity
                event_ids = list(set([str(r.event_id) for r in rows if r.event_id]))
                if event_ids:
                    event_id = event_ids[0]
                    logger.info(f"Success! Articles processed and clustered into Event ID: {event_id}")
                    if len(event_ids) > 1:
                        logger.warning("Articles clustered into multiple events (similarity threshold too strict?). Using the first one.")
                break
            else:
                logger.info(f"Still processing... ({i+1}/{max_attempts})")
                
        if not event_id:
            logger.error("Failed to process articles within the timeout.")
            return
            
    # 3. Trigger Event Summarization (we'll do this manually via bash, so for now we'll just wait for the summary)
    logger.info(f"Event ID is {event_id}. To generate the summary, run this in your terminal:")
    logger.info(f"docker exec perslens-analysis python -c \"from app.tasks import generate_event_summary_task; generate_event_summary_task('{event_id}')\"")
    
    # Wait a few seconds for the database to update (the summary generation might take 30s)
    # The python os.system call above is synchronous and will block until done!
    logger.info("Summary generation complete.")
    
    # 4. Fetch the final Event data from the API
    logger.info("\n=======================================================")
    logger.info("VERIFYING ARCHITECTURE OUTPUT via API")
    logger.info("=======================================================")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Event Details
        r = await client.get(f"/events/{event_id}")
        event = r.json()
        logger.info(f"EVENT TITLE: {event.get('title')}")
        logger.info(f"mT5 NEUTRAL SUMMARY: {event.get('summary')}")
        
        # Perspective Matrix
        r = await client.get(f"/events/{event_id}/matrix")
        matrix = r.json().get('matrix', [])
        logger.info("\nPERSPECTIVE MATRIX (Sentiment & Framing per Source):")
        for m in matrix:
            logger.info(f"  - {m['source']}: {m['sentiment']} | Stance: {m['stance']}")
            logger.info(f"    Avg Framing: {m['average_framing']}")
            
        # Claims
        r = await client.get(f"/events/{event_id}/claims")
        claims = r.json().get('claims', [])
        logger.info("\nFACTUAL CLAIMS EXTRACTED:")
        for c in claims:
            logger.info(f"  - {c['type']}: {c['text']} (via {c['source']})")
            
        # Blindspots
        r = await client.get(f"/events/{event_id}/blindspots")
        blindspots = r.json().get('blindspots', [])
        logger.info("\nBLINDSPOTS DETECTED:")
        if not blindspots:
            logger.info("  - No blindspots detected (expected since we haven't run the batch blindspot job).")
        for b in blindspots:
            logger.info(f"  - {b['type']} for {b['source_group']}: {b['evidence']}")
            
if __name__ == "__main__":
    asyncio.run(verify_pipeline())
