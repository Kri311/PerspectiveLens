import math
from typing import List, Dict, Tuple
from collections import Counter

def tokenize(text: str) -> List[str]:
    """Basic tokenizer for Tamil text."""
    # In a production environment, you would use indic-nlp-library or spacy
    import re
    # Remove punctuation and split by whitespace
    text = re.sub(r'[^\w\s]', '', text.lower())
    return [word for word in text.split() if len(word) > 2]

def compute_log_odds_ratio(
    corpus_a: List[str], 
    corpus_b: List[str], 
    prior_corpus: List[str] = None
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Computes the log-odds-ratio with an informative Dirichlet prior.
    This surfaces words that are uniquely over-represented in Corpus A vs Corpus B.
    
    Args:
        corpus_a: List of documents from source group A.
        corpus_b: List of documents from source group B.
        prior_corpus: Background corpus (usually A + B).
        
    Returns:
        Two dictionaries: top words for A, and top words for B with their z-scores.
    """
    if prior_corpus is None:
        prior_corpus = corpus_a + corpus_b
        
    # Count word frequencies
    freq_a = Counter()
    for doc in corpus_a:
        freq_a.update(tokenize(doc))
        
    freq_b = Counter()
    for doc in corpus_b:
        freq_b.update(tokenize(doc))
        
    freq_prior = Counter()
    for doc in prior_corpus:
        freq_prior.update(tokenize(doc))
        
    # Total word counts
    n_a = sum(freq_a.values())
    n_b = sum(freq_b.values())
    n_prior = sum(freq_prior.values())
    
    if n_a == 0 or n_b == 0 or n_prior == 0:
        return {}, {}

    z_scores = {}
    
    for word, count_prior in freq_prior.items():
        if count_prior < 2:  # Ignore very rare words
            continue
            
        count_a = freq_a.get(word, 0)
        count_b = freq_b.get(word, 0)
        
        # Dirichlet Prior
        # The prior size dictates how much we trust the background distribution
        alpha = (count_prior / n_prior) * n_prior 
        
        # Log odds formula with Dirichlet smoothing
        odds_a = (count_a + alpha) / (n_a + alpha - (count_a + alpha))
        odds_b = (count_b + alpha) / (n_b + alpha - (count_b + alpha))
        
        log_odds = math.log(odds_a) - math.log(odds_b)
        
        # Variance calculation for z-score normalization
        var_a = 1.0 / (count_a + alpha)
        var_b = 1.0 / (count_b + alpha)
        variance = var_a + var_b
        
        z_score = log_odds / math.sqrt(variance)
        z_scores[word] = z_score

    # Words with positive z-scores lean towards A, negative towards B
    top_a = {w: score for w, score in sorted(z_scores.items(), key=lambda item: item[1], reverse=True)[:20] if score > 1.96}
    top_b = {w: abs(score) for w, score in sorted(z_scores.items(), key=lambda item: item[1])[:20] if score < -1.96}
    
    return top_a, top_b
