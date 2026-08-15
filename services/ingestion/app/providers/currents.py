import os
import requests
from typing import List, Dict, Any
from dateutil import parser
import logging
from app.providers.base import NewsProvider

logger = logging.getLogger(__name__)

class CurrentsAPIProvider(NewsProvider):
    """
    Fetches news from Currents API.
    """
    
    BASE_URL = "https://api.currentsapi.services/v1/search"
    
    def __init__(self):
        self.api_key = os.getenv("CURRENTS_API_KEY")
        if not self.api_key:
            logger.warning("CURRENTS_API_KEY is not set.")
    
    def fetch(self, query: str = "தமிழ்நாடு", language: str = "ta", limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
            
        params = {
            "apiKey": self.api_key,
            "keywords": query,
            "language": language,
            "limit": min(limit, 20)
        }
        
        logger.info(f"Fetching from Currents API for query: {query}")
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get("news", []):
                try:
                    published_at = parser.parse(item.get("published"))
                    
                    # Currents API returns full content if available. We can potentially use it directly
                    # or still rely on our trafilatura fallback if we only have the URL.
                    
                    article_data = {
                        'url': item.get("url"),
                        'title': item.get("title"),
                        'published_at': published_at.isoformat(),
                        'description': item.get("description", ""),
                        'source_name': item.get("author") or "Currents API Unknown" 
                    }
                    articles.append(article_data)
                except Exception as e:
                    logger.error(f"Error parsing Currents API entry: {e}")
                    
            return articles
        except Exception as e:
            logger.error(f"Currents API request failed: {e}")
            return []
