import logging
import threading
from transformers import pipeline
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class NLPModels:
    _instance = None
    
    def __init__(self):
        self.embedding_model = None
        self.ner_pipeline = None
        self.nli_pipeline = None
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_embedding_model(self):
        with self._lock:
            if self.embedding_model is None:
                logger.info("Loading SBERT model (l3cube-pune/tamil-sentence-similarity-sbert)...")
                self.embedding_model = SentenceTransformer('l3cube-pune/tamil-sentence-similarity-sbert')

    def load_ner_model(self):
        with self._lock:
            if not hasattr(self, 'ner_pipeline') or self.ner_pipeline is None:
                logger.info("Loading NER model (Babelscape/wikineural-multilingual-ner)...")
                self.ner_pipeline = pipeline(
                    "ner", 
                    model="Babelscape/wikineural-multilingual-ner", 
                    aggregation_strategy="simple"
                )

    def load_zero_shot_model(self):
        with self._lock:
            if not hasattr(self, 'zero_shot_pipeline') or self.zero_shot_pipeline is None:
                logger.info("Loading Zero-Shot model (MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli)...")
                self.zero_shot_pipeline = pipeline(
                    "zero-shot-classification",
                    model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli"
                )

    def load_nli_model(self):
        with self._lock:
            if not hasattr(self, 'nli_pipeline') or self.nli_pipeline is None:
                logger.info("Loading NLI model (MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli)...")
                self.nli_pipeline = pipeline(
                    "text-classification",
                    model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",
                    return_all_scores=True
                )


    def get_embedding(self, text: str) -> list[float]:
        self.load_embedding_model()
        # encode returns a numpy array, we convert to python list
        return self.embedding_model.encode(text).tolist()

    def get_entities(self, text: str) -> list[dict]:
        self.load_ner_model()
            
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
        self.load_zero_shot_model()
        try:
            result = self.zero_shot_pipeline(text, candidate_labels=candidate_labels, multi_label=False)
            return {
                "sequence": result.get("sequence", text),
                "labels": result.get("labels", candidate_labels),
                "scores": [float(s) for s in result.get("scores", [1.0 / len(candidate_labels)] * len(candidate_labels))]
            }
        except Exception as e:
            logger.error(f"Zero-shot classification error: {e}")
            # Fallback to uniform distribution
            n = len(candidate_labels)
            return {
                "sequence": text,
                "labels": candidate_labels,
                "scores": [1.0 / n] * n
            }
        
    def get_nli(self, premise: str, hypothesis: str) -> dict:
        self.load_nli_model()
        try:
            input_text = f"{premise} [SEP] {hypothesis}"
            result = self.nli_pipeline(input_text)
            
            # result is a list of lists of dicts: [[{"label": ..., "score": ...}, ...]]
            scores_list = result[0] if isinstance(result[0], list) else result
            
            label_map = {
                "ENTAILMENT": "ENTAILMENT",
                "NEUTRAL": "NEUTRAL", 
                "CONTRADICTION": "CONTRADICTION",
                "entailment": "ENTAILMENT",
                "neutral": "NEUTRAL",
                "contradiction": "CONTRADICTION",
            }
            
            distribution = {}
            for item in scores_list:
                label = label_map.get(item["label"], item["label"].upper())
                distribution[label] = float(item["score"])
            
            prediction = max(distribution, key=distribution.get)
            
            return {
                "prediction": prediction,
                "confidence": distribution[prediction],
                "distribution": distribution
            }
        except Exception as e:
            logger.error(f"NLI error: {e}")
            return {
                "prediction": "ENTAILMENT",
                "confidence": 0.33,
                "distribution": {"ENTAILMENT": 0.33, "NEUTRAL": 0.34, "CONTRADICTION": 0.33}
            }

nlp_models = NLPModels.get_instance()
