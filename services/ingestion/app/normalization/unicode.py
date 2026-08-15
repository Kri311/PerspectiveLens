import unicodedata

def normalize_tamil_text(text: str) -> str:
    """
    Applies Unicode NFC normalization to text.
    This ensures that visually identical Tamil characters are represented
    by the same underlying byte sequence, preventing mismatch issues
    in hashing, embedding, and deduplication.
    """
    if not text:
        return ""
    # NFC (Normalization Form Canonical Composition) is the standard
    # for web text and most NLP pipelines.
    return unicodedata.normalize('NFC', text).strip()
