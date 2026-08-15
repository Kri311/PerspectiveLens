# Phase 2 Implementation Log

## Overview
This document logs the work completed during Phase 2: Event Discovery & Story Clustering for PerspectiveLens.

## Actions Taken
1. **Bug Fix**:
   - Fixed `ModuleNotFoundError: No module named 'asyncpg'` in the ingestion worker by changing `DATABASE_URL` in `.env` to use the synchronous `postgresql://` driver, as our worker relies on synchronous SQLAlchemy.
2. **NLP Engine Service**:
   - Created `services/nlp-engine/Dockerfile` and `requirements.txt` (CPU PyTorch).
   - Created `services/nlp-engine/app/models.py` with Singleton pattern to lazy-load `l3cube-pune/tamil-sentence-similarity-sbert` (Embeddings) and `l3cube-pune/tamil-ner` (NER).
   - Created FastAPI application in `services/nlp-engine/app/main.py` with `/embed` and `/ner` POST endpoints.
3. **Analysis Worker Service**:
   - Created `services/analysis-worker/Dockerfile` and `requirements.txt` (Celery, pgvector).
   - Setup `services/analysis-worker/app/database.py` with SQLAlchemy models, including `Event` and `ArticleEntity` with pgvector definitions.
   - Created `services/analysis-worker/app/tasks.py` which fetches queued articles, requests embeddings/NER, and performs vector cosine similarity search in Postgres to resolve stories into Events.
   - Configured Celery beat schedule to run the analysis task every 5 minutes.
4. **Docker Integration**:
   - Updated `docker-compose.yml` to include `nlp-engine` and `analysis-worker`.
   - Mapped `./model_cache` to `/root/.cache/huggingface` to prevent re-downloading models across container restarts.

## Status
All Phase 2 tasks are structurally complete.
- **Verification Note**: Manual verification by the user is required to start the docker containers (`docker compose up --build -d`) due to sandbox restrictions in the AI agent environment preventing Docker commands.
