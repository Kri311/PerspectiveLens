from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class MT5Summarizer:
    def __init__(self):
        self.pipeline = None

    def load_model(self):
        if self.pipeline is None:
            logger.info("Loading mT5 Summarization model (csebuetnlp/mT5_multilingual_XLSum)...")
            self.pipeline = pipeline("summarization", model="csebuetnlp/mT5_multilingual_XLSum")

    def summarize(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        if self.pipeline is None:
            self.load_model()
            
        try:
            # We enforce limits to prevent excessive memory/CPU consumption on CPU-only machines
            result = self.pipeline(text, max_length=max_length, min_length=min_length, truncation=True)
            return result[0]['summary_text']
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return ""

# Singleton instance
summarizer_instance = MT5Summarizer()
