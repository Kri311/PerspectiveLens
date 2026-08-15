import os
import logging
import requests
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from celery import shared_task
from app.database import SessionLocal, Article, Event, ArticleEntity, ArticleAnalysis, Claim, Entity
from app.claims.extraction import extract_claims_heuristic
from app.claims.nli_comparison import compare_claims

logger = logging.getLogger(__name__)

NLP_ENGINE_URL = os.getenv("NLP_ENGINE_URL", "http://nlp-engine:8001")
SIMILARITY_THRESHOLD = 0.82  # Cosine similarity threshold for event matching

def get_embedding(text: str) -> Optional[List[float]]:
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/embed", json={"text": text}, timeout=60)
        resp.raise_for_status()
        return resp.json().get("embedding")
    except Exception as e:
        logger.error(f"Error getting embedding from NLP engine: {e}")
        return None

def get_entities(text: str) -> List[Dict]:
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/ner", json={"text": text}, timeout=60)
        resp.raise_for_status()
        return resp.json().get("entities", [])
    except Exception as e:
        logger.error(f"Error getting NER from NLP engine: {e}")
        return []

def get_sentiment(text: str) -> Dict:
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/sentiment", json={"text": text}, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error getting sentiment from NLP engine: {e}")
        return {}

def get_framing(text: str) -> Dict:
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/framing", json={"text": text}, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error getting framing from NLP engine: {e}")
        return {}

def get_stance(text: str, target_entity: str) -> Dict:
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/stance", json={"text": text, "target_entity": target_entity}, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error getting stance from NLP engine: {e}")
        return {}

def resolve_event(db: Session, article: Article, embedding: List[float]) -> Event:
    """
    Finds the most similar existing event using pgvector cosine distance (<=>).
    If similarity > SIMILARITY_THRESHOLD, append to event.
    Otherwise, create a new event.
    Note: cosine_distance = 1 - cosine_similarity. So similarity > 0.82 means distance < 0.18.
    """
    distance_threshold = 1.0 - SIMILARITY_THRESHOLD
    
    # We use raw SQL with pgvector to find the closest event
    query = text("""
        SELECT id, representative_title as title, centroid_embedding <=> :embedding AS distance
        FROM events
        WHERE centroid_embedding <=> :embedding < :threshold
        ORDER BY distance ASC
        LIMIT 1
    """)
    
    result = db.execute(query, {
        "embedding": str(embedding),
        "threshold": distance_threshold
    }).fetchone()
    
    if result:
        logger.info(f"Matched article to existing event: {result.id} (distance: {result.distance:.3f})")
        event = db.query(Event).filter(Event.id == result.id).first()
        return event
    else:
        logger.info("No matching event found. Creating new event.")
        new_event = Event(
            representative_title=article.title,
            summary=article.description or article.title,
            image_url=article.image_url,
            centroid_embedding=embedding
        )
        db.add(new_event)
        db.flush() # flush to get the ID
        return new_event

@shared_task(bind=True, max_retries=3)
def process_queued_articles(self):
    """
    Finds articles in 'queued' status, gets embeddings/NER, resolves events.
    """
    db: Session = SessionLocal()
    processed_count = 0
    
    try:
        # Get up to 50 queued articles at a time
        articles = db.query(Article).filter(Article.status == 'queued').limit(50).all()
        
        if not articles:
            logger.info("No queued articles to process.")
            return {"processed": 0}
            
        for article in articles:
            logger.info(f"Processing article: {article.id}")
            
            # Use title + lead paragraph for embeddings (more dense information)
            body_text = article.body or ""
            text_to_embed = f"{article.title}. {body_text[:500]}"
            
            # 1. Get Embedding
            embedding = get_embedding(text_to_embed)
            if not embedding:
                logger.warning(f"Failed to get embedding for {article.id}")
                continue
                
            # No content_embedding column in articles, skipping assignment
            
            # 2. Get Entities
            entities_data = get_entities(text_to_embed)
            
            # Map NER output to DB enum
            ner_type_map = {
                'PER': 'PERSON',
                'ORG': 'ORGANIZATION',
                'LOC': 'LOCATION',
                'MISC': 'EVENT'
            }
            
            for ent in entities_data:
                canonical_name = ent['word'].strip()
                ner_type = ent['entity_group']
                mapped_type = ner_type_map.get(ner_type, 'EVENT')
                
                # Upsert Entity
                db_ent = db.query(Entity).filter(Entity.canonical_name == canonical_name).first()
                if not db_ent:
                    db_ent = Entity(canonical_name=canonical_name, entity_type=mapped_type)
                    db.add(db_ent)
                    db.flush()
                
                # Store ArticleEntity linking
                db_article_entity = ArticleEntity(
                    article_id=article.id,
                    entity_id=db_ent.id,
                    surface_form=canonical_name,
                    confidence=ent['score'],
                    position=ent['start']
                )
                db.add(db_article_entity)
            
            # 3. Resolve Event
            event = resolve_event(db, article, embedding)
            article.event_id = event.id
            article.status = 'processed'
            
            # 4. Sentiment and Framing
            sentiment_data = get_sentiment(text_to_embed)
            framing_data = get_framing(text_to_embed)
            
            # 5. Stance Analysis (Determine primary entity first)
            primary_entity = None
            if entities_data:
                # Find best PERSON or ORG (or default to highest score)
                best_ents = sorted(entities_data, key=lambda x: x['score'], reverse=True)
                primary_entity = best_ents[0]['word']
                
            stance_data = {}
            if primary_entity:
                stance_data = get_stance(text_to_embed, primary_entity)
            
            # Save analysis
            analysis = ArticleAnalysis(
                article_id=article.id,
                model_version='mDeBERTa-v3-base-mnli-xnli',
                sentiment=sentiment_data.get('sentiment'),
                sentiment_confidence=sentiment_data.get('confidence'),
                frame_distribution=framing_data.get('distribution', {}),
                stance=stance_data.get('stance'),
                stance_confidence=stance_data.get('confidence')
            )
            db.add(analysis)
            
            # 6. Claim Extraction
            entities_list = [e['word'] for e in entities_data] if entities_data else []
            extracted_claims = extract_claims_heuristic(text_to_embed, entities_list)
            
            for claim_dict in extracted_claims:
                db_claim = Claim(
                    event_id=event.id,
                    article_id=article.id,
                    claim_text=claim_dict['claim_text'],
                    claim_type=claim_dict['claim_type'],
                    confidence=claim_dict['confidence']
                )
                db.add(db_claim)
            
            db.commit()
            processed_count += 1
            
            # Enqueue summary generation now that claims are added
            generate_event_summary_task.delay(str(event.id))
            
        logger.info(f"Analysis worker processed {processed_count} articles.")
        return {"processed": processed_count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing articles: {e}")
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()

@shared_task
def generate_event_summary_task(event_id: str):
    """Generates an event summary using extracted claims."""
    with SessionLocal() as db:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return
            
        claims = db.query(Claim).filter(Claim.event_id == event_id).all()
        if not claims:
            return
            
        from app.summary.event_summary import generate_evidence_based_summary
        summary = generate_evidence_based_summary(claims)
        
        if summary:
            event.summary = summary
            db.commit()
            logger.info(f"Generated summary for event {event_id}")
