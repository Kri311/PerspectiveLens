# Phase 4: Blindspot & Claim Analysis

## Overview
Phase 4 expands the platform's analytical capabilities by introducing factual claim extraction, Natural Language Inference (NLI) to detect contradictions, and the signature "Blindspot" detection algorithm.

## Implementation Details

### 1. NLI Engine (`/nli`)
The `mDeBERTa-v3` model utilized in Phase 3 was originally trained on the Multi-Genre NLI (MNLI/XNLI) dataset. By exposing a `/nli` endpoint in our NLP engine, we can pass it a "Premise" (Claim A) and a "Hypothesis" (Claim B) in Tamil. The model natively outputs whether the claims result in `ENTAILMENT` (agreement), `CONTRADICTION`, or are `NEUTRAL`.

### 2. Claim Extraction Heuristics
Located at `services/analysis-worker/app/claims/extraction.py`, this script serves as a lightweight alternative to generative LLM-based claim extraction. 
* It tokenizes Tamil articles into distinct sentences.
* It filters for sentences that contain prominent Named Entities (extracted via the `wikineural-multilingual-ner` model).
* These sentences are isolated and stored in the database as discrete "Claims".

### 3. Three-Level Blindspot Detection
The core Blindspot algorithm (`services/analysis-worker/app/blindspots/detection.py`) analyzes the Coverage Matrix to find media gaps:
* **Level 1 (Event Gap)**: Identifies if an entire source group (e.g., Dravidian media) heavily covered an event (>60% of articles) while another group completely ignored it (<5% of articles).
* **Level 2 (Entity Gap)**: Identifies if a specific entity (e.g., a politician) was frequently mentioned globally for an event, but intentionally omitted by a specific source group.
* **Level 3 (Aspect Gap)**: Identifies if source groups heavily disagree on the framing of an event (e.g., one group frames it as "Economic", while another frames it as "Controversy/Scandal").

### 4. API Integration
The intelligence gathered by the worker is exposed via standard REST endpoints:
* `GET /blindspots`: A global feed returning all active blindspot candidates across all events, ranked by severity score.
* `GET /events/{id}/claims`: Returns all factual claims and NLI contradiction relations for a specific event.
* `GET /events/{id}/blindspots`: Returns blindspots detected for a specific event.

## Status
✅ Phase 4 is Fully Implemented.
