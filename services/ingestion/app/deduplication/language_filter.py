import os
import fasttext
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("FASTTEXT_MODEL_PATH", "/app/models/lid.176.bin")

# Lazily load model to avoid memory overhead if not used
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = fasttext.load_model(MODEL_PATH)
        except Exception as e:
            logger.error(f"Failed to load fastText model from {MODEL_PATH}: {e}")
            raise
    return _model

def is_tamil(text: str, threshold: float = 0.5) -> bool:
    """
    Validates if the provided text is predominantly Tamil.
    Returns True if Tamil ('__label__ta') is the top predicted language
    with confidence >= threshold.
    """
    if not text or not text.strip():
        return False
        
    try:
        model = get_model()
        # Fasttext expects a single line of text
        clean_text = text.replace('\n', ' ').strip()
        if not clean_text:
            return False
            
        predictions = model.predict(clean_text, k=1)
        top_label = predictions[0][0]
        confidence = predictions[1][0]
        
        return top_label == '__label__ta' and confidence >= threshold
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        # Default to True on failure if we can't be sure, to not drop data?
        # Actually safer to drop if we are strictly Tamil, but let's be strict.
        return False
