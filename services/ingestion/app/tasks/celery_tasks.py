import logging
import requests
import os
import uuid
import shutil
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from celery import shared_task
from dateutil import parser
from app.database import SessionLocal, Article, Source
from app.providers.google_news import GoogleNewsRSSProvider
from app.providers.newsdata import NewsDataIOProvider
from app.providers.gnews import GNewsIOProvider
from app.providers.currents import CurrentsAPIProvider
from app.providers.rss_outlets import TamilTVRSSProvider
from app.normalization.boilerplate import extract_article_text
from app.normalization.unicode import normalize_tamil_text
from app.deduplication.language_filter import is_tamil
from app.deduplication.hashing import generate_content_hash, generate_url_hash
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_og_image(html_content: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    except Exception:
        pass
    return None

def download_image(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=5)
        if response.status_code == 200:
            ext = url.split('.')[-1].split('?')[0]
            if len(ext) > 4 or not ext.isalnum():
                ext = 'jpg'
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join('/app/media', filename)
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            # Return absolute URL for frontend consumption
            return f"http://localhost:8000/media/{filename}"
    except Exception as e:
        logger.error(f"Failed to download image {url}: {e}")
    return url  # Fallback to remote URL if download fails

import re

# Canonical source name mapping for deduplication
_SOURCE_ALIASES = {
    "daily thanthi": "Daily Thanthi",
    "dailythanthi": "Daily Thanthi",
    "thanthi": "Daily Thanthi",
    "\u0ba4\u0bbf\u0ba9\u0ba4\u0bcd\u0ba4\u0ba8\u0bcd\u0ba4\u0bbf": "Daily Thanthi",
    "dinamalar": "Dinamalar",
    "\u0ba4\u0bbf\u0ba9\u0bae\u0bb2\u0bb0\u0bcd": "Dinamalar",
    "vikatan": "Vikatan",
    "\u0bb5\u0bbf\u0b95\u0b9f\u0ba9\u0bcd": "Vikatan",
    "dinamani": "Dinamani",
    "\u0ba4\u0bbf\u0ba9\u0bae\u0ba3\u0bbf": "Dinamani",
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

def _normalize_source_name(name: str) -> str:
    """Normalize source name to canonical form."""
    if not name:
        return name
    lookup = name.strip().lower()
    lookup_clean = re.sub(r'\s*(news|tv|online|digital|web)\s*$', '', lookup).strip()
    return _SOURCE_ALIASES.get(lookup, _SOURCE_ALIASES.get(lookup_clean, name.strip().title()))

def get_or_create_source(db: Session, source_name: str) -> Source:
    canonical_name = _normalize_source_name(source_name)
    source = db.query(Source).filter(Source.name == canonical_name).first()
    if not source:
        # Also check with the raw name in case it was stored before normalization
        source = db.query(Source).filter(Source.name == source_name).first()
        if source:
            # Update the name to canonical form
            source.name = canonical_name
            db.commit()
            db.refresh(source)
        else:
            # Assign logical default orientation based on known Tamil news outlets
            orientation = "OTHER_UNKNOWN"
            cn_lower = canonical_name.lower()
            if any(w in cn_lower for w in ["sun", "kalaignar", "murasoli", "dinakaran"]):
                orientation = "DRAVIDIAN_ORIENTED"
            elif any(w in cn_lower for w in ["jaya", "namadhu amma"]):
                orientation = "AIADMK_ORIENTED"
            elif any(w in cn_lower for w in ["dinamalar", "janam", "thamarai"]):
                orientation = "CONSERVATIVE_VARIABLE"
            elif any(w in cn_lower for w in ["thanthi", "polimer", "puthiya", "hindu", "news18", "zee", "asianet", "abp", "dinamani", "vikatan", "samayam", "oneindia", "bbc"]):
                orientation = "OTHER_UNKNOWN"
                
            source = Source(name=canonical_name, orientation=orientation)
            db.add(source)
            db.commit()
            db.refresh(source)
    return source

def fetch_html(url: str) -> Optional[str]:
    try:
        # Avoid getting blocked by basic bots protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Google News RSS URLs are often redirects, resolve them
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch HTML for {url}: {e}")
        return None

def process_articles(provider_name: str, articles_data: list):
    db: Session = SessionLocal()
    success_count = 0
    skip_count = 0
    
    try:
        for data in articles_data:
            url = data['url']
            
            # Check if URL already exists
            if db.query(Article).filter(Article.url == url).first():
                skip_count += 1
                continue
                
            # Fetch raw HTML
            html = fetch_html(url)
            if not html:
                skip_count += 1
                continue
                
            # Extract boilerplate-free text
            raw_text = extract_article_text(html)
            
            # Normalize unicode
            clean_text = normalize_tamil_text(raw_text)
            
            # Validate language
            if not is_tamil(clean_text):
                logger.info(f"Skipping non-Tamil or low-confidence article: {url}")
                skip_count += 1
                continue
                
            # Generate deduplication hash
            content_hash = generate_content_hash(clean_text)
            if not content_hash:
                skip_count += 1
                continue
                
            # Check for exact content duplicate across all sources
            if db.query(Article).filter(Article.content_hash == content_hash).first():
                logger.info(f"Skipping content duplicate: {url}")
                skip_count += 1
                continue
                
            # Source resolution
            source_name = data.get('source_name') or f'{provider_name} Unknown'
            source = get_or_create_source(db, source_name)
            
            # Extract high quality image from meta tags if RSS didn't provide one
            image_url = data.get('image_url')
            if not image_url or image_url.strip() == "":
                image_url = extract_og_image(html)
            
            # Download the image locally to avoid hotlinking
            if image_url:
                image_url = download_image(image_url)
            
            # Insert into database
            article = Article(
                source_id=source.id,
                url=url,
                title=data.get('title'),
                description=data.get('description'),
                body=clean_text,
                image_url=image_url,
                language='ta',
                published_at=parser.parse(data['published_at']),
                content_hash=content_hash,
                status='queued'
            )
            
            try:
                db.add(article)
                db.commit()
                success_count += 1
                logger.info(f"Ingested new article from {provider_name}: {url}")
            except IntegrityError:
                db.rollback()
                logger.warning(f"Integrity error (likely duplicate URL) for {url}")
                skip_count += 1
                
    finally:
        db.close()
        
    logger.info(f"{provider_name} fetch complete. Ingested: {success_count}, Skipped: {skip_count}")
    return {"ingested": success_count, "skipped": skip_count}

@shared_task(bind=True)
def fetch_google_news(self):
    logger.info("Starting Google News RSS fetch for specific outlets...")
    provider = GoogleNewsRSSProvider()
    queries = ["தமிழ்நாடு", "sun news", "thanthi tv", "polimer news", "puthiya thalaimurai", "news18 tamil"]
    
    total_ingested = 0
    total_skipped = 0
    for q in queries:
        articles_data = provider.fetch(query=q, limit=20)
        res = process_articles(f"Google News RSS ({q})", articles_data)
        total_ingested += res.get("ingested", 0)
        total_skipped += res.get("skipped", 0)
        
    return {"ingested": total_ingested, "skipped": total_skipped}

@shared_task(bind=True)
def fetch_newsdata_io(self):
    logger.info("Starting NewsData.io API fetch...")
    provider = NewsDataIOProvider()
    articles_data = provider.fetch(query="தமிழ்நாடு", limit=10)
    return process_articles("NewsData.io API", articles_data)

@shared_task(bind=True)
def fetch_gnews_io(self):
    logger.info("Starting GNews.io API fetch...")
    provider = GNewsIOProvider()
    articles_data = provider.fetch(query="தமிழ்நாடு", limit=10)
    return process_articles("GNews.io API", articles_data)

@shared_task(bind=True)
def fetch_currents_api(self):
    logger.info("Starting Currents API fetch...")
    provider = CurrentsAPIProvider()
    articles_data = provider.fetch(query="தமிழ்நாடு", limit=10)
    return process_articles("Currents API", articles_data)

@shared_task(bind=True)
def fetch_tamil_tv_rss(self):
    """Fetch RSS feeds from Tamil TV news outlets (Sun News, Thanthi TV, etc.)."""
    logger.info("Starting Tamil TV RSS outlet fetch...")
    provider = TamilTVRSSProvider()
    articles_data = provider.fetch(limit_per_outlet=15)
    return process_articles("Tamil TV RSS", articles_data)
