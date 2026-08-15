import os
import requests
from typing import List, Dict, Any
from dateutil import parser
import logging
from app.providers.base import NewsProvider

logger = logging.getLogger(__name__)

class NewsDataIOProvider(NewsProvider):
    """
    Fetches news from NewsData.io API.
    """
    
    BASE_URL = "https://newsdata.io/api/1/latest"
    
    def __init__(self):
        self.api_key = os.getenv("NEWS_DATA_API_KEY")
        if not self.api_key:
            logger.warning("NEWS_DATA_API_KEY is not set.")
    
    def fetch(self, query: str = "தமிழ்நாடு", language: str = "ta", limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
            
        params = {
            "apikey": self.api_key,
            "q": query,
            "language": language,
            "size": min(limit, 50)  # max 50 per request
        }
        
        logger.info(f"Fetching from NewsData.io API for query: {query}")
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get("results", []):
                try:
                    published_at = parser.parse(item.get("pubDate"))
                    
                    article_data = {
                        'url': item.get("link"),
                        'title': item.get("title"),
                        'published_at': published_at.isoformat(),
                        'description': item.get("description", ""),
                        'image_url': item.get("image_url", ""),
                        'source_name': item.get("source_id", "NewsData.io Unknown")
                    }
                    articles.append(article_data)
                except Exception as e:
                    logger.error(f"Error parsing NewsData.io entry: {e}")
                    
            return articles
        except Exception as e:
            logger.error(f"NewsData.io API request failed: {e}")
            return []
