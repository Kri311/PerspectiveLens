from abc import ABC, abstractmethod
from typing import List, Dict, Any

class NewsProvider(ABC):
    """
    Abstract base class for all news providers.
    Any new source (Google News, NewsData.io, RSS feeds, etc.) must implement this interface.
    """
    
    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches articles from the provider.
        Returns a list of dictionaries. Each dictionary should contain at least:
        - 'url': The canonical URL of the article
        - 'title': The title of the article
        - 'published_at': Datetime string of publication
        - 'raw_html': Optional. The raw HTML content (if the provider supports full text)
        """
        pass
