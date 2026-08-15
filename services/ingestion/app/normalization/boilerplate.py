import trafilatura
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_article_text(html_content: str) -> str:
    """
    Extracts the main article body from raw HTML, stripping out navigation menus,
    footers, ads, and other boilerplate.
    
    Falls back to a simple BeautifulSoup extraction if trafilatura fails.
    """
    if not html_content:
        return ""
        
    try:
        # Trafilatura is excellent at finding the main text content of news articles
        extracted = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=False,
            include_images=False,
            no_fallback=False
        )
        if extracted:
            return extracted
            
        # Fallback to simple BeautifulSoup text extraction
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
        
        text = soup.get_text(separator='\n')
        # Collapse multiple newlines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""
