import os
import requests
import logging

logger = logging.getLogger(__name__)
NLP_ENGINE_URL = os.getenv("NLP_ENGINE_URL", "http://nlp-engine:8001")

def generate_evidence_based_summary(claims: list) -> str:
    """
    Takes a list of claims/evidence from the database, structures them,
    and calls the NLP Engine to generate a neutral summary.
    """
    if not claims:
        return ""
        
    # We create a structured prompt to prevent hallucination
    evidence_text = " ".join([c.claim_text for c in claims[:5]])
    
    prompt = f"Summarize the following facts neutrally in Tamil: {evidence_text}"
    
    try:
        resp = requests.post(f"{NLP_ENGINE_URL}/summarize", json={
            "text": prompt,
            "max_length": 100
        }, timeout=60)
        resp.raise_for_status()
        
        return resp.json().get("summary", "")
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return ""
