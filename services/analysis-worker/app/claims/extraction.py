import re
from typing import List, Dict

def extract_claims_heuristic(text: str, entities: List[str]) -> List[str]:
    """
    Heuristic claim extraction for MVP.
    Splits text into sentences, and if a sentence contains a known entity,
    it is considered a "Claim".
    """
    claims = []
    
    # Very basic sentence splitting (Tamil punctuation similar to English)
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20: # Too short to be a factual claim
            continue
            
        # Check if any important entity is in this sentence
        for entity in entities:
            if entity in sentence:
                claims.append({
                    "claim_text": sentence,
                    "claim_type": "ENTITY_RELATION",
                    "confidence": 0.75 # Heuristic confidence
                })
                break # Move to next sentence
                
    return claims
