import os
import requests
import logging
from typing import Dict

logger = logging.getLogger(__name__)
NLP_ENGINE_URL = os.getenv("NLP_ENGINE_URL", "http://nlp-engine:8001")

def compare_claims(claim_a: str, claim_b: str) -> Dict:
    """
    Uses the NLI Engine to compare two claims.
    Returns ENTAILMENT, NEUTRAL, or CONTRADICTION.
    """
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/nli", json={
            "premise": claim_a,
            "hypothesis": claim_b
        }, timeout=10)
        resp.raise_for_status()
        
        result = resp.json()
        
        # Determine specific conflict type if contradiction
        conflict_type = None
        if result['prediction'] == 'CONTRADICTION':
            # In a full implementation, we would use NER to see if they disagree on DATE, NUMERIC, or PERSON
            # For MVP, we default to CHARACTERIZATION
            conflict_type = 'CHARACTERIZATION'
            
        return {
            "relation": result['prediction'],
            "confidence": result['confidence'],
            "conflict_type": conflict_type
        }
    except Exception as e:
        logger.error(f"Error calling NLI engine: {e}")
        return {}
