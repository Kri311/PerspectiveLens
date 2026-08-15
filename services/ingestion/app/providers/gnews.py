import os
import requests
from typing import List, Dict, Any
from dateutil import parser
import logging
from app.providers.base import NewsProvider

logger = logging.getLogger(__name__)

class GNewsIOProvider(NewsProvider):
    """
    Fetches news from GNews.io API.
    """
    
    BASE_URL = "https://gnews.io/api/v4/search"
    
    def __init__(self):
        self.api_key = os.getenv("GNEWS_API_KEY")
        if not self.api_key:
            logger.warning("GNEWS_API_KEY is not set.")
    
    def fetch(self, query: str = "தமிழ்நாடு", language: str = "ta", limit: int = 20, **kwargs) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []
            
        params = {
            "token": self.api_key,
            "q": query,
            "lang": language,
            "max": min(limit, 100),
            "sortby": "publishedAt"
        }
        
        logger.info(f"Fetching from GNews.io API for query: {query}")
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get("articles", []):
                try:
                    published_at = parser.parse(item.get("publishedAt"))
                    
                    source_name = "GNews Unknown"
                    if "source" in item and "name" in item["source"]:
                        source_name = item["source"]["name"]

                    article_data = {
                        'url': item.get("url"),
                        'title': item.get("title"),
                        'published_at': published_at.isoformat(),
                        'description': item.get("description", ""),
                        'source_name': source_name
                    }
                    articles.append(article_data)
                except Exception as e:
                    logger.error(f"Error parsing GNews.io entry: {e}")
                    
            return articles
        except Exception as e:
            logger.error(f"GNews.io API request failed: {e}")
            return []
