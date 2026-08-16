import feedparser
import requests
from typing import List, Dict, Any
from urllib.parse import quote
from datetime import datetime
from dateutil import parser as dateparser
from bs4 import BeautifulSoup
import logging
from app.providers.base import NewsProvider

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Mapping: RSS feed URLs → canonical source name
#
# For outlets WITHOUT native RSS feeds we route
# through the Google News RSS search endpoint.
# For outlets WITH native feeds we hit them directly.
# ─────────────────────────────────────────────

TAMIL_TV_OUTLETS = {
    # ── Google News RSS proxy (no native feed) ──
    "Sun News":            "https://news.google.com/rss/search?q=site:sunnews.in+OR+%22Sun+News%22&hl=ta&gl=IN&ceid=IN:ta",
    "Kalaignar TV":        "https://news.google.com/rss/search?q=%22Kalaignar+TV%22+OR+%22Kalaignar+News%22&hl=ta&gl=IN&ceid=IN:ta",
    "Jaya TV":             "https://news.google.com/rss/search?q=%22Jaya+TV%22+OR+%22Jaya+Plus%22&hl=ta&gl=IN&ceid=IN:ta",
    "Thanthi TV":          "https://news.google.com/rss/search?q=site:thanthitv.com+OR+%22Thanthi+TV%22&hl=ta&gl=IN&ceid=IN:ta",
    "Polimer News":        "https://news.google.com/rss/search?q=%22Polimer+News%22+OR+%22Polimer%22&hl=ta&gl=IN&ceid=IN:ta",
    "Puthiya Thalaimurai": "https://news.google.com/rss/search?q=%22Puthiya+Thalaimurai%22&hl=ta&gl=IN&ceid=IN:ta",
    "News18 Tamil":        "https://news.google.com/rss/search?q=%22News18+Tamil%22&hl=ta&gl=IN&ceid=IN:ta",
    "News7 Tamil":         "https://news.google.com/rss/search?q=%22News7+Tamil%22&hl=ta&gl=IN&ceid=IN:ta",
    "Daily Thanthi":       "https://news.google.com/rss/search?q=site:dailythanthi.com+OR+%22Daily+Thanthi%22&hl=ta&gl=IN&ceid=IN:ta",

    # ── Native RSS feeds ──
    "Dinamalar":           "https://rss.dinamalar.com/?cat=ara1", # politics
    "Dinamalar Top":       "https://rss.dinamalar.com/?cat=top1", # top news
    "Vikatan":             "https://www.vikatan.com/stories.rss",
    "OneIndia Tamil":      "https://tamil.oneindia.com/rss/feeds/oneindia-tamil-fb.xml",
    "Samayam Tamil":       "https://tamil.samayam.com/rssfeedsdefault.cms",
    "Hindu Tamil":         "https://www.hindutamil.in/rss/tamilnadu",
    "BBC Tamil":           "https://feeds.bbci.co.uk/tamil/rss.xml",
    "Zee Tamil News":      "https://zeenews.india.com/tamil/rss/tamil-nadu.xml",
    "Asianet News Tamil":  "https://tamil.asianetnews.com/rss/news",
    "Dinamani":            "https://www.dinamani.com/tamilnadu/rssfeed/?id=118",
    "Dinakaran":           "https://www.dinakaran.com/feed/",
    "ABP Nadu":            "https://tamil.abplive.com/home/feed",
}


def _extract_og_image_from_url(url: str) -> str:
    """Try to pull og:image from a page for better thumbnails."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            og = soup.find('meta', property='og:image')
            if og and og.get('content'):
                return og['content']
    except Exception:
        pass
    return ""


class TamilTVRSSProvider(NewsProvider):
    """
    Aggregates RSS feeds from multiple Tamil TV news outlets.
    For outlets that don't publish native RSS, we use the Google News
    RSS search endpoint filtered to that outlet's site/name.
    """

    def fetch(self, limit_per_outlet: int = 15, **kwargs) -> List[Dict[str, Any]]:
        all_articles = []

        for outlet_name, feed_url in TAMIL_TV_OUTLETS.items():
            try:
                logger.info(f"Fetching RSS feed for {outlet_name}: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:limit_per_outlet]:
                    try:
                        # Parse published date
                        pub_str = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
                        if pub_str:
                            published_at = dateparser.parse(pub_str)
                        else:
                            published_at = datetime.utcnow()

                        # ── Image extraction (priority order) ──
                        image_url = ""
                        # 1) media:content
                        if hasattr(entry, 'media_content') and entry.media_content:
                            image_url = entry.media_content[0].get('url', '')
                        # 2) media:thumbnail
                        if not image_url and hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                            image_url = entry.media_thumbnail[0].get('url', '')
                        # 3) enclosure
                        if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
                            for enc in entry.enclosures:
                                if enc.get('type', '').startswith('image'):
                                    image_url = enc.get('href', '') or enc.get('url', '')
                                    break
                        # 4) <img> inside description / summary HTML
                        if not image_url:
                            summary_html = getattr(entry, 'summary', '') or ''
                            if '<img' in summary_html:
                                soup = BeautifulSoup(summary_html, 'html.parser')
                                img_tag = soup.find('img')
                                if img_tag and img_tag.get('src'):
                                    image_url = img_tag['src']

                        # Resolve Google News redirect for the source name
                        source_name = outlet_name
                        if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                            source_name = entry.source.title  # use actual publisher if Google News provides it

                        # Clean description text (strip HTML)
                        description = getattr(entry, 'summary', '') or ''
                        if '<' in description:
                            description = BeautifulSoup(description, 'html.parser').get_text(separator=' ', strip=True)

                        article_data = {
                            'url': entry.link,
                            'title': entry.title,
                            'published_at': published_at.isoformat(),
                            'description': description[:500],
                            'image_url': image_url,
                            'source_name': source_name,
                        }
                        all_articles.append(article_data)

                    except Exception as e:
                        logger.error(f"Error parsing RSS entry for {outlet_name}: {e}")

            except Exception as e:
                logger.error(f"Failed to fetch feed for {outlet_name}: {e}")

        logger.info(f"TamilTVRSSProvider fetched {len(all_articles)} articles total")
        return all_articles
