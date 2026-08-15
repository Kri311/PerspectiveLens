import logging
from transformers import pipeline
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class NLPModels:
    _instance = None
    
    def __init__(self):
        self.embedding_model = None
        self.ner_pipeline = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_models(self):
        """
        Lazy load models to save memory until they are actually needed,
        or load them once on startup.
        """
        if self.embedding_model is None:
            logger.info("Loading SBERT model (l3cube-pune/tamil-sentence-similarity-sbert)...")
            # This model is optimized for Tamil sentence similarity
            self.embedding_model = SentenceTransformer('l3cube-pune/tamil-sentence-similarity-sbert')
            
        if not hasattr(self, 'ner_pipeline') or self.ner_pipeline is None:
            logger.info("Loading NER model (Babelscape/wikineural-multilingual-ner)...")
            # This model detects entities
            self.ner_pipeline = pipeline(
                "ner", 
                model="Babelscape/wikineural-multilingual-ner", 
                aggregation_strategy="simple"
            )
            
        if not hasattr(self, 'zero_shot_pipeline') or self.zero_shot_pipeline is None:
            logger.info("Loading Zero-Shot model (MoritzLaurer/mDeBERTa-v3-base-mnli-xnli)...")
            # Multilingual zero-shot classification for sentiment and framing
            self.zero_shot_pipeline = pipeline(
                "zero-shot-classification",
                model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
            )
            
        if not hasattr(self, 'nli_pipeline') or self.nli_pipeline is None:
            logger.info("Loading NLI model (MoritzLaurer/mDeBERTa-v3-base-mnli-xnli)...")
            # Multilingual Natural Language Inference (Premise vs Hypothesis)
            self.nli_pipeline = pipeline(
                "text-classification",
                model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
                return_all_scores=True
            )
            
        logger.info("Models loaded successfully.")

    def get_embedding(self, text: str) -> list[float]:
        if self.embedding_model is None:
            self.load_models()
        # encode returns a numpy array, we convert to python list
        return self.embedding_model.encode(text).tolist()

    def get_entities(self, text: str) -> list[dict]:
        if self.ner_pipeline is None:
            self.load_models()
            
        # The aggregation_strategy="simple" attempts to group sub-words into full entities
        raw_entities = self.ner_pipeline(text)
        
        # Format the output to be JSON serializable (numpy types to native python)
        clean_entities = []
        for ent in raw_entities:
            clean_entities.append({
                "word": ent.get("word"),
                "entity_group": ent.get("entity_group"),
                "score": float(ent.get("score", 0.0)),
                "start": int(ent.get("start", 0)),
                "end": int(ent.get("end", 0))
            })
            
        return clean_entities

    def get_classification(self, text: str, candidate_labels: list[str]) -> dict:
        if getattr(self, 'zero_shot_pipeline', None) is None:
            self.load_models()
            
        result = self.zero_shot_pipeline(text, candidate_labels)
        
        # Format the output cleanly
        return {
            "labels": result.get("labels", []),
            "scores": [float(score) for score in result.get("scores", [])]
        }
        
    def get_nli(self, premise: str, hypothesis: str) -> dict:
        if getattr(self, 'nli_pipeline', None) is None:
            self.load_models()
            
        # NLI pipeline takes dict {"text": premise, "text_pair": hypothesis}
        result = self.nli_pipeline({"text": premise, "text_pair": hypothesis})
        
        # Result is list of list: [[{'label': 'entailment', 'score': 0.9}]]
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
            scores = result[0]
        else:
            scores = result
            
        formatted_scores = {item['label'].upper(): float(item['score']) for item in scores}
        
        # Determine top label
        top_label = max(formatted_scores.items(), key=lambda x: x[1])
        
        return {
            "prediction": top_label[0],
            "confidence": top_label[1],
            "distribution": formatted_scores
        }

nlp_models = NLPModels.get_instance()
