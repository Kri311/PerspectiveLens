# Phase 3: Framing Analysis & Perspective Matrix

## Overview
Phase 3 establishes the core intelligence layer of PerspectiveLens. It focuses on taking raw, ingested text and understanding the subtle nuances of *how* a story is being told. We extract the overall sentiment, calculate the specific media frames being used, and determine the stance of the article towards key political figures or entities.

## Implementation Details

### 1. Zero-Shot Classification Engine (`mDeBERTa-v3`)
Rather than fine-tuning a model like MuRIL from scratch (which requires massive labeled datasets and GPU compute), we leveraged **Zero-Shot Classification** using `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`.
* **Why this model?**: It natively understands over 100 languages, including Tamil, and provides highly accurate classifications without needing explicit fine-tuning.
* **Sentiment Analysis**: The model is prompted to classify Tamil text into `Positive`, `Negative`, or `Neutral`.
* **Framing Classification**: The text is classified against 6 primary frames: Economic, Political Strategy, Policy/Achievement, Social Justice, Law and Order, Controversy/Scandal. We opted for 6 frames instead of 11 to avoid probability dilution in a zero-shot context.

### 2. Stance Analysis
The Celery `analysis-worker` extracts the most prominent `PERSON` or `ORGANIZATION` from the text using a multilingual NER model. It then sends this target entity and the article text to the NLP Engine's `/stance` endpoint. 
The zero-shot engine evaluates: *"The stance of this text towards {Target Entity} is [Support, Oppose, Neutral]"*.

### 3. Lexical Bias (Log-Odds Ratio)
Located at `services/analysis-worker/app/lexical/log_odds.py`, this script implements the **Log-Odds Ratio with an Informative Dirichlet Prior**. It compares the frequency of words used by one political cohort (e.g., Dravidian media) versus another (e.g., Conservative media) to mathematically surface the most uniquely "loaded" words or dog whistles.

### 4. Contrastive Learning (Triplet Loss)
While not used for real-time inference, the training loop and Triplet Loss architecture for Contrastive Learning is documented at `services/nlp-engine/app/framing/contrastive_training.py`. This serves as the foundation if we choose to fine-tune our own embeddings later.

### 5. Perspective Matrix API
The core feature, accessible via `GET /events/{event_id}/matrix`, aggregates the Sentiment, Framing, and Stance of all articles covering a specific event, grouping them by the news source. This provides the exact JSON schema required to build Ground News-style "Orientation Bars".

## Status
✅ Phase 3 is Fully Implemented.
