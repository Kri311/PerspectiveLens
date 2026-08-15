import hashlib
from typing import Optional

def generate_content_hash(text: str) -> Optional[str]:
    """
    Generates a SHA-256 hash of the content for exact deduplication.
    Assumes text has already been Unicode NFC normalized.
    """
    if not text:
        return None
    
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def generate_url_hash(url: str) -> Optional[str]:
    """
    Generates a SHA-256 hash of the URL.
    Can be used if URLs are very long or need to be indexed efficiently.
    (Though our DB has a UNIQUE constraint on the URL string itself).
    """
    if not url:
        return None
        
    return hashlib.sha256(url.encode('utf-8')).hexdigest()
