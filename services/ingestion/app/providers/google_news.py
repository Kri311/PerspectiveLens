import feedparser
import requests
from typing import List, Dict, Any
from urllib.parse import quote
from datetime import datetime
from dateutil import parser
import logging
from app.providers.base import NewsProvider

logger = logging.getLogger(__name__)

class GoogleNewsRSSProvider(NewsProvider):
    """
    Fetches news from Google News RSS feeds using a specific query.
    """
    
    BASE_URL = "https://news.google.com/rss/search?q={query}&hl=ta&gl=IN&ceid=IN:ta"
    
    def fetch(self, query: str = "தமிழ்நாடு", limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        encoded_query = quote(query)
        url = self.BASE_URL.format(query=encoded_query)
        
        logger.info(f"Fetching RSS feed from: {url}")
        feed = feedparser.parse(url)
        
        articles = []
        for entry in feed.entries[:limit]:
            try:
                published_at = parser.parse(entry.published) if hasattr(entry, 'published') else datetime.utcnow()
                
                # We do not fetch the full text here. We will fetch the HTML by visiting the link.
                article_data = {
                    'url': entry.link,
                    'title': entry.title,
                    'published_at': published_at.isoformat(),
                    'description': entry.summary if hasattr(entry, 'summary') else "",
                    'source_name': entry.source.title if hasattr(entry, 'source') else ""
                }
                articles.append(article_data)
            except Exception as e:
                logger.error(f"Error parsing RSS entry: {e}")
                
        return articles
