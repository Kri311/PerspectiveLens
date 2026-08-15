# PerspectiveLens — Complete System Architecture

> **An event-centric Tamil news intelligence architecture for multi-source semantic aggregation, media-framing comparison, claim-level disagreement analysis, and coverage-blindspot detection.**

**Project Type:** Product-based Text Analytics / NLP Platform
**Primary Language:** Tamil
**Primary Domain:** Tamil Nadu News Media
**Project Name:** PerspectiveLens

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Objective](#2-product-objective)
3. [Core Design Principles](#3-core-design-principles)
4. [High-Level System Flow](#4-high-level-system-flow)
5. [NLP Model Stack](#5-nlp-model-stack)
6. [Docker Microservices Architecture](#6-docker-microservices-architecture)
7. [Data Ingestion Layer](#7-data-ingestion-layer)
8. [Preprocessing Pipeline](#8-preprocessing-pipeline)
9. [Data Layer & Storage](#9-data-layer--storage)
10. [Tamil NLP Engine](#10-tamil-nlp-engine)
11. [Event Resolution & Similarity](#11-event-resolution--similarity)
12. [Story Clustering](#12-story-clustering)
13. [Story Timeline](#13-story-timeline)
14. [Named Entity Recognition & Normalization](#14-named-entity-recognition--normalization)
15. [Framing Engine](#15-framing-engine)
16. [Claim Analysis Engine](#16-claim-analysis-engine)
17. [Blindspot Engine](#17-blindspot-engine)
18. [Source Intelligence Layer](#18-source-intelligence-layer)
19. [Event Summary Engine](#19-event-summary-engine)
20. [Database Schema](#20-database-schema)
21. [API Architecture](#21-api-architecture)
22. [Frontend Architecture](#22-frontend-architecture)
23. [Search Architecture](#23-search-architecture)
24. [Async Processing & Queuing](#24-async-processing--queuing)
25. [Complete Processing Flow](#25-complete-processing-flow)
26. [Model Versioning & Caching](#26-model-versioning--caching)
27. [Security](#27-security)
28. [Repository Structure](#28-repository-structure)
29. [Training Data Strategy](#29-training-data-strategy)
30. [Evaluation Framework](#30-evaluation-framework)
31. [Research Experiments](#31-research-experiments)
32. [Technology Stack Summary](#32-technology-stack-summary)
33. [Development Phases](#33-development-phases)
34. [Ethical Guardrails](#34-ethical-guardrails)

---

## 1. Executive Summary

PerspectiveLens is an **event-centric** Tamil multi-source news intelligence platform. The architecture is intentionally designed around real-world events rather than publisher-bias labels.

The system does **not** begin by asking:

> *"Is this article pro-DMK or pro-AIADMK?"*

It begins by asking:

> *"Which real-world event is this article describing?"*

Only **after** articles are grouped into the same event does the system compare:

- **Stance** — support / oppose / neutral toward key actors
- **Sentiment** — positive / negative / neutral tone
- **Framing** — achievement, criticism, controversy, etc.
- **Lexical choices** — loaded or slanted word usage
- **Claims** — agreement, contradiction, conflict types
- **Entities** — who is mentioned or omitted
- **Coverage** — which publishers covered or ignored the event
- **Source orientation** — long-term publisher editorial leaning

This event-first philosophy prevents publisher labels from contaminating event discovery, ensuring analytical integrity.

```
                         ┌──────────────────────────┐
                         │      TAMIL NEWS SOURCES  │
                         │                          │
                         │ Google News / RSS        │
                         │ NewsData.io              │
                         │ Currents API             │
                         │ Optional fallback feeds  │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │      INGESTION WORKER     │
                         │                          │
                         │ Fetch → Normalize →      │
                         │ Validate → Deduplicate → │
                         │ Rate-limit               │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │     DATA / VECTOR STORE   │
                         │                          │
                         │ PostgreSQL + pgvector    │
                         │ + JSONB                  │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                    ┌──────────────────────────────────┐
                    │           TAMIL NLP ENGINE         │
                    │                                  │
                    │ Language Detection               │
                    │ Sentence Embeddings             │
                    │ Named Entity Recognition         │
                    │ Stance / Sentiment / Framing     │
                    └────────────────┬─────────────────┘
                                     │
                    ┌────────────────┼─────────────────┐
                    │                │                 │
                    ▼                ▼                 ▼
              Embeddings         Entities        Linguistic
                                                Representations
                    │                │                 │
                    └────────────────┼─────────────────┘
                                     ▼
                         ┌──────────────────────────┐
                         │     EVENT RESOLUTION      │
                         │                          │
                         │ Vector retrieval         │
                         │ Entity overlap            │
                         │ Temporal similarity       │
                         │ Keyword overlap           │
                         │ Location overlap          │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │    STORY CLUSTERING       │
                         │                          │
                         │ kNN similarity graph     │
                         │ Leiden / Louvain         │
                         │ HDBSCAN for experiments  │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │       STORY TIMELINE      │
                         └────────────┬─────────────┘
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
        ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
        │ FRAMING ENGINE │   │ CLAIM ENGINE   │   │ COVERAGE ENGINE│
        │                │   │                │   │                │
        │ Stance         │   │ NLI            │   │ Event coverage │
        │ Sentiment      │   │ Agreement      │   │ Entity coverage│
        │ Frame labels   │   │ Contradiction  │   │ Aspect coverage│
        │ Lexical bias   │   │ Conflict types │   │ Blindspots     │
        └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
                │                    │                    │
                └────────────────────┼────────────────────┘
                                     ▼
                         ┌──────────────────────────┐
                         │   SOURCE INTELLIGENCE    │
                         │                          │
                         │ Source orientation       │
                         │ Ownership                │
                         │ Reliability metadata     │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │    SUMMARY ENGINE         │
                         │                          │
                         │ Evidence-grounded        │
                         │ Neutral event summary    │
                         │ Agreement / disagreement │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │       FASTAPI REST API    │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │         FRONTEND          │
                         │                          │
                         │ Event Timeline           │
                         │ Perspective Matrix       │
                         │ Blindspot Feed            │
                         │ Source Profile            │
                         │ Ownership Transparency    │
                         └──────────────────────────┘
```

---

## 2. Product Objective

The platform is a **Tamil-language multi-source news intelligence system**. A user should be able to open any event and see:

1. **All relevant Tamil reports** belonging to that event
2. **A unified chronology** (story timeline)
3. **Which publishers** covered the event
4. **Which source-orientation groups** covered it
5. **How the framing differs** between outlets
6. **Which claims are agreed upon** across sources
7. **Which claims conflict** between sources
8. **Which entities or aspects** are emphasized or omitted
9. **Potential coverage blindspots**
10. **Publisher ownership and orientation information**
11. **A neutral, event-level summary**

### Core Product Principle

> **Show the information landscape around an event, not a single publisher's interpretation of it.**

---

## 3. Core Design Principles

### 3.1 Event-First Discovery

Articles are grouped by real-world event **before** any political comparison.

```
Article → Event Resolution → Story Cluster → Framing Comparison
```

### 3.2 Bias Is Multi-Dimensional

The system never reduces an article to a single binary label. It separates:

| Dimension | Description |
|---|---|
| **Source Orientation** | Long-term publisher editorial leaning (metadata) |
| **Article Framing** | How *this specific article* presents the event |
| **Stance** | Support / Oppose / Neutral toward a target entity |
| **Sentiment** | Positive / Negative / Neutral tone |
| **Lexical Signals** | Loaded or slanted word choices |
| **Claim Disagreements** | Factual contradictions across sources |
| **Coverage Gaps** | Events, entities, or aspects ignored by a source group |

### 3.3 Source Orientation Is Transparent Metadata

Publisher orientation is stored as a reviewable, evidence-backed source attribute — not a classifier prediction.

**Tamil Nadu Media Orientation Categories:**

| Category | Example Outlets |
|---|---|
| `DRAVIDIAN_ORIENTED` | Sun News, Kalaignar TV |
| `AIADMK_ORIENTED` | Jaya TV, Jaya News |
| `CONSERVATIVE_VARIABLE` | Thanthi TV, Dinamalar |
| `POPULIST_SENSATIONAL` | Polimer News |
| `OTHER_UNKNOWN` | Unclassified / Independent |

Each source record also stores:

```
label                   → orientation category
confidence              → 0.0 – 1.0
evidence / reference    → external media-monitoring source
last_reviewed           → date of last human review
review_notes            → context / justification
```

### 3.4 Hybrid Analytical Approach

```
Unsupervised discovery        → semantic similarity, event clusters, recurring frames
     +
Human-defined source metadata → orientation labels, ownership records
     +
Supervised NLP models         → stance, sentiment, framing classifiers
     +
Human validation              → annotation review, threshold tuning
```

Unsupervised methods **discover patterns**; they cannot independently determine political meaning without reference labels.

### 3.5 Explainability Is Required

Every major analytical output must surface its evidence chain:

```
Framing:   High criticism
Evidence:
  - criticism-related lexical terms detected
  - high opposition-response frame probability (0.68)
  - stance toward target = OPPOSE (0.74 confidence)
```

---

## 4. High-Level System Flow

The entire system is captured by **four core questions**:

### Question 1 — WHAT happened?

```
Embeddings + NER + Event Resolution + Clustering
```

### Question 2 — HOW is it being described?

```
Stance + Sentiment + Framing + Lexical Analysis
```

### Question 3 — WHERE do reports disagree?

```
Claims + NLI + Conflict Classification
```

### Question 4 — WHAT is missing?

```
Coverage Matrix + Entity Coverage + Aspect Coverage + Blindspot Ranking
```

Then **Source Intelligence** (orientation, ownership, reliability metadata) provides contextual information.

**One-Line Pipeline:**

```
INGEST → NORMALIZE → EMBED/NER → RESOLVE EVENTS → CLUSTER STORIES
→ ANALYZE FRAMING/CLAIMS → ANALYZE COVERAGE → DETECT BLINDSPOTS
→ ADD SOURCE INTELLIGENCE → SUMMARIZE → SERVE VIA FASTAPI
```

---

## 5. NLP Model Stack

### 5.1 Definitive Model Selections

| NLP Task | Model | Rationale |
|---|---|---|
| **Language Detection** | `fastText lid.176` | Fast Tamil validation before expensive NLP processing |
| **Sentence Embeddings** | `l3cube-pune/tamil-sentence-similarity-sbert` | Fine-tuned for Semantic Textual Similarity; optimal for grouping sentences about identical real-world events |
| **Embedding Benchmark** | `l3cube-pune/indic-sentence-similarity-sbert` | Secondary comparison for multi-lingual evaluation |
| **Entity Extraction (NER)** | `ai4bharat/IndicNER` | Pre-trained on Indian entities; accurately extracts Tamil political figures, parties, and locations |
| **Stance & Framing** | `google/muril-base-cased` (fine-tuned) | Handles Tamil-English code-mixing in news headlines better than other models |
| **Sentiment** | MuRIL fine-tuned | Positive / Negative / Neutral classification |
| **Bias Backbone (Classification)** | `ai4bharat/IndicBERTv2-MLM-Sam-TLM` | Outperforms others on pure in-language classification tasks |
| **NLI (Claim Analysis)** | IndicBERT / MuRIL fine-tuned | Claim agreement / contradiction detection |
| **Lexical Bias** | Log-Odds Ratio (Dirichlet Prior) + TF-IDF + Character N-grams | Surfaces uniquely "loaded" words overused by specific cohorts |
| **Summarization** | `csebuetnlp/mT5_multilingual_XLSum` | Abstractive summarizer trained natively on 44 languages including Tamil |
| **Optional LLM** | Llama-family Tamil-capable model | Advanced generation (later phase only) |

### 5.2 Lexical Analysis Configuration

```
Word n-grams:      1–2
Character n-grams: 3–5
Methods:           TF-IDF + character n-gram TF-IDF + log-odds ratio
```

**Log-Odds Formula** (isolates editorial bias signal between two publisher cohorts $i$ and $j$):

$$\text{LogOdds} = \log\frac{y_{w}^{i} + \alpha_w}{n_i + \alpha_0 - y_{w}^{i} - \alpha_w} - \log\frac{y_{w}^{j} + \alpha_w}{n_j + \alpha_0 - y_{w}^{j} - \alpha_w}$$

### 5.3 NLP Engine Endpoints

The engine should expose internal endpoints:

```
POST /embed       → sentence embeddings
POST /ner         → named entity recognition
POST /stance      → stance classification
POST /sentiment   → sentiment classification
POST /framing     → frame classification
POST /analyze     → batch multi-task processing (efficiency)
```

---

## 6. Docker Microservices Architecture

### 6.1 Seven-Container MVP

| # | Container | Technology | Role |
|---|---|---|---|
| 1 | `postgres` | PostgreSQL + pgvector | Source of truth: articles, NER tags, vectors, factuality scores. HNSW index for cosine similarity search |
| 2 | `redis` | Redis | Message broker for async Celery tasks + short-lived cache |
| 3 | `ingestion-worker` | FastAPI + Celery | Handles API rate limits, CRON-scheduled data fetching, cleaning, deduplication. Pushes payloads to Redis queue |
| 4 | `nlp-engine` | FastAPI + PyTorch (GPU) | Heavy lifter — hosts embedding models, IndicNER, MuRIL classifiers. Consumes from Redis queue, generates vectors & stance predictions |
| 5 | `analysis-worker` | Python + Celery | Mathematical engine — HDBSCAN/Leiden clustering, event resolution, claim analysis, blindspot Jaccard similarity, coverage matrix updates |
| 6 | `api` | FastAPI | Public-facing backend — REST endpoints, user auth, serves Timeline View, Blindspot Feed, Perspective Matrix |
| 7 | `frontend` | React / Next.js | User interface — Event Timeline, Perspective Matrix, Blindspot Feed, Source Profiles |

### 6.2 Optional Later Services

| Service | Purpose |
|---|---|
| Nginx | Reverse proxy / load balancer |
| MinIO | Object storage for raw payloads, HTML snapshots, model outputs |
| Monitoring | Metrics, logging, alerting |

### 6.3 Container Interaction Diagram

```
                           ┌───────────────┐
                           │   Frontend    │
                           └───────┬───────┘
                                   │
                                   ▼
                           ┌───────────────┐
                           │    FastAPI    │
                           └───────┬───────┘
                                   │
                    ┌──────────────┼───────────────┐
                    │              │               │
                    ▼              ▼               ▼
              PostgreSQL        Redis         NLP Engine
              + pgvector                        (GPU)
                    ▲                              │
                    │                     ┌────────┼────────┐
                    │                     │        │        │
                    │                     ▼        ▼        ▼
                    │                  Embedding  NER   Classifiers
                    │
                    ▲
                    │
             ┌──────┴────────┐
             │ Analysis      │
             │ Worker        │
             │               │
             │ Event         │
             │ Clustering    │
             │ Claims        │
             │ Coverage      │
             │ Blindspots    │
             │ Lexical       │
             └──────▲────────┘
                    │
             ┌──────┴────────┐
             │ Ingestion     │
             │ Worker        │
             └───────────────┘
                    ▲
                    │
       ┌────────────┼────────────┐
       │            │            │
   Google News   NewsData    Currents
```

> **Design Decision:** Start with a single GPU-oriented NLP service. Do **not** begin with 10+ microservices, Kubernetes, Kafka, separate vector databases, or multiple message brokers. They add infrastructure complexity without improving the first working version.

---

## 7. Data Ingestion Layer

### 7.1 News Sources

**Initial Sources:**

| Provider | Type | Notes |
|---|---|---|
| Google News / RSS | RSS Feed | Primary Tamil news aggregator |
| NewsData.io | REST API | Free tier with Tamil language filter |
| Currents API | REST API | Free tier with regional filter |

**Optional Fallback Sources:**

```
GDELT
Publisher-specific RSS feeds
Other legal feeds / APIs
```

### 7.2 Provider-Independent Architecture

The ingestion system uses a pluggable provider pattern:

```
NewsProvider (abstract)
├── GoogleNewsProvider
├── NewsDataProvider
├── CurrentsProvider
└── OptionalFallbackProvider
```

This means the NLP system **never needs to know** where an article came from. Adding a new source is a matter of implementing the provider interface.

### 7.3 Ingestion Workflow

```
API / RSS
   ↓
Fetch
   ↓
Rate-limit check (per-provider schedule)
   ↓
Raw response
   ↓
Schema normalization (provider → canonical format)
   ↓
Language detection (fastText lid.176 — Tamil validation)
   ↓
Unicode normalization (NFC)
   ↓
HTML / boilerplate removal
   ↓
URL deduplication (URL hash)
   ↓
Content deduplication (content hash)
   ↓
Near-duplicate detection (title similarity)
   ↓
Store article in PostgreSQL
   ↓
Queue NLP job in Redis
```

---

## 8. Preprocessing Pipeline

### 8.1 Unicode Normalization

Apply **Unicode NFC normalization** to all Tamil text. This prevents equivalent Tamil strings from being represented differently at the byte level, which would cause false mismatches in embedding and deduplication.

### 8.2 Boilerplate Removal

Strip from raw HTML:

- HTML markup and tags
- Navigation menus
- Advertisements
- Footer / header text
- Social sharing buttons
- Unrelated article recommendations

**Candidate Libraries:**

```
trafilatura        → primary recommendation (robust article extraction)
BeautifulSoup      → fine-grained HTML parsing fallback
newspaper3k        → newspaper-style extraction
```

### 8.3 Language Validation

Use `fastText lid.176` to validate that text is Tamil or acceptable Tamil-English code-mixed text **before** expensive NLP processing. Reject non-Tamil content early.

### 8.4 Multi-Level Deduplication

| Level | Method | Purpose |
|---|---|---|
| 1 | URL hash | Exact URL matches |
| 2 | Content hash (SHA-256) | Identical article body |
| 3 | Title similarity (cosine) | Republished with minor edits |
| 4 | Near-duplicate similarity | Syndicated copies across outlets |

A syndicated copy must **not** create multiple independent NLP analyses.

---

## 9. Data Layer & Storage

### 9.1 Primary Stack

| Technology | Purpose |
|---|---|
| **PostgreSQL** | Source of truth — articles, entities, events, claims, analysis results |
| **pgvector** | Semantic similarity, nearest-neighbor retrieval, event candidate generation, semantic search |
| **JSONB** | Flexible NLP outputs — NER results, frame probabilities, stance probabilities, lexical signatures, claim metadata |
| **Redis** | Message broker (Celery), short-lived query cache |

### 9.2 pgvector Configuration

```sql
embedding VECTOR(D)    -- D must match embedding model dimension
```

Create an **HNSW cosine similarity index** on the vector column.

> **Important:** Do not hard-code `768` for the dimension until the model checkpoint has been finalized. The dimension `D` must match the selected embedding model output.

### 9.3 Raw Data Storage

**MVP:** PostgreSQL JSONB is sufficient for storing raw API payloads.

**Later (optional):** Add **MinIO** for:

- Raw API payloads
- Raw HTML snapshots
- Article archives
- Model outputs and checkpoints

This allows NLP models to be re-run without re-downloading articles.

### 9.4 Article Data Model

Each article stores:

```
article_id          → UUID primary key
source_id           → FK to sources table
url                 → original URL
canonical_url       → normalized/canonical URL
title               → article headline
description         → article summary / snippet
body                → full article text
language            → detected language code
author              → author name(s)
published_at        → publication timestamp
collected_at        → ingestion timestamp
content_hash        → SHA-256 of body for dedup
title_hash          → hash of title for near-dedup
status              → processing status (queued/processed/failed)
raw_payload         → original API response (JSONB)
created_at          → record creation timestamp
updated_at          → last update timestamp
```

Additional NLP fields are stored separately in versioned analysis tables.

---

## 10. Tamil NLP Engine

The NLP engine is the main **GPU-capable service**. It is a single container hosting all models for simplicity of deployment and debugging.

### 10.1 Components

```
┌──────────────────────────────────────┐
│          TAMIL NLP ENGINE            │
│                                      │
│  Language Detection (fastText)       │
│  Tamil Sentence Embeddings (SBERT)   │
│  IndicNER (entity extraction)        │
│  MuRIL (stance, sentiment)           │
│  Framing Classifier (MuRIL/IndicBERT)│
│  NLI Model (claim analysis)         │
└──────────────────────────────────────┘
```

### 10.2 Embedding Pipeline

```
Article
   ↓
Title + Lead / important sentences
   ↓
Tamil Sentence Similarity SBERT
   ↓
Dense vector
   ↓
pgvector (stored)
```

**Stored embedding types:**

| Type | Description |
|---|---|
| `TITLE` | Embedding of headline only |
| `LEAD` | Embedding of title + first paragraph |
| `CHUNK` | Embedding of body chunk (optional, later) |
| `ARTICLE` | Full article embedding (optional, later) |

> **Priority:** Start with title + lead text embeddings. Full article chunk embeddings can be added after the event resolution system works.

---

## 11. Event Resolution & Similarity

Event resolution is the **first major analytical stage** — determining which real-world event a new article describes.

### 11.1 Resolution Workflow

```
New article
   ↓
Generate embedding (SBERT)
   ↓
Search pgvector (cosine similarity, top-k)
   ↓
Retrieve top-k similar articles
   ↓
Compare composite event evidence
   ↓
Assign to existing event OR create new event
```

### 11.2 Composite Event Similarity Formula

$$\text{EventSimilarity} = w_1 \times \text{Semantic}(A, B) + w_2 \times \text{Entity}(E_A, E_B) + w_3 \times \text{Temporal}(T_A, T_B) + w_4 \times \text{Keyword}(A, B) + w_5 \times \text{Location}(L_A, L_B)$$

**Initial weights (to be tuned):**

| Signal | Weight | Description |
|---|---|---|
| Semantic similarity | 0.55 | Cosine similarity of SBERT embeddings |
| Entity overlap | 0.20 | Jaccard similarity of NER entity sets |
| Temporal similarity | 0.10 | Decay function on time difference |
| Keyword overlap | 0.10 | TF-IDF keyword intersection |
| Location overlap | 0.05 | Shared location entity match |

> **Critical:** These weights are initial engineering estimates. They **must be tuned** using a manually labeled event-pair validation set. Do not permanently hard-code a threshold (e.g., `0.78`) without validation.

### 11.3 Event Assignment Logic

```python
if event_similarity >= tuned_threshold:
    attach_article_to_existing_event()
elif score_is_close_to_threshold:
    mark_as_uncertain()
    send_to_secondary_analysis()
else:
    create_candidate_new_event()
```

The uncertain zone prevents aggressive false clustering.

### 11.4 Why Event Embeddings Are Central

The system must distinguish:

- **Same event, different wording** (should cluster together)
- **Different events, similar subject** (should remain separate)

Example:

```
Article A: "Government launches a new scheme."
Article B: "Chief Minister announces a new welfare plan."
Article C: "Opposition criticizes the newly announced scheme."
```

All three may describe **one event**. The embedding layer provides semantic candidate retrieval; NER and temporal signals then verify the match.

---

## 12. Story Clustering

### 12.1 Primary Production Approach — Graph Clustering

```
pgvector nearest-neighbor search
         ↓
kNN graph (articles as nodes, similarity as edges)
         ↓
Similarity-weighted edges
         ↓
Leiden / Louvain community detection
         ↓
Story clusters
```

**Why graph clustering?** News stories evolve over time and may contain transitive chains:

```
A ≈ B,  B ≈ C,  C ≈ D    (but A ≉ D directly)
```

Graph clustering handles this chained structure naturally, without requiring every document to be equally close.

### 12.2 HDBSCAN (Supporting Role)

HDBSCAN is supported for:

- Experiments & model benchmarking
- Offline dataset analysis
- Exploratory visualization
- Comparing cluster quality metrics

It is **not** the primary real-time event engine.

### 12.3 Why Not K-Means?

K-Means requires specifying the number of clusters in advance. The number of daily news stories is **unknown and variable**. K-Means should not be the primary story clustering algorithm.

---

## 13. Story Timeline

Once a story cluster is established:

```
Story ID
   │
   ├── Article A  (10:00 AM)
   ├── Article B  (11:15 AM)
   ├── Article C  (12:30 PM)
   ├── Article D  (02:10 PM)
   └── Article E  (04:45 PM)
```

Articles within a cluster are sorted by `published_at`.

**Stored timeline metadata:**

```
first_seen          → timestamp of first article
last_updated        → timestamp of most recent article
source_count        → number of distinct publishers
article_count       → total articles in the cluster
```

The story timeline is the **central product object** — everything else (framing, claims, coverage, blindspots) hangs off it.

---

## 14. Named Entity Recognition & Normalization

### 14.1 NER Model

**Base model:** `ai4bharat/IndicNER`

**Fine-tuning:** Further fine-tune on a small manually labeled Tamil political-news dataset.

**Recommended custom entity classes:**

| Entity Type | Examples |
|---|---|
| `PERSON` | மு.க.ஸ்டாலின், எடப்பாடி பழனிசாமி |
| `ORGANIZATION` | தேர்தல் ஆணையம் |
| `POLITICAL_PARTY` | திமுக, அதிமுக, பாஜக |
| `LOCATION` | சென்னை, தமிழ்நாடு |
| `GOVERNMENT_BODY` | சட்டப்பேரவை |
| `POLICY` | புதிய கல்விக் கொள்கை |
| `LAW` | தடுப்பு கோரிக்கை சட்டம் |
| `SCHEME` | நலத்திட்டம் |
| `COMPANY` | அதானி குழுமம் |
| `EVENT` | உள்ளாட்சித் தேர்தல் |
| `DATE` | 2025 ஜனவரி |

### 14.2 Entity Normalization

Different articles can refer to the same entity using different surface forms:

```
மு.க.ஸ்டாலின்   →  canonical: MK_STALIN
முதல்வர் ஸ்டாலின்  →  canonical: MK_STALIN
ஸ்டாலின்          →  canonical: MK_STALIN
```

**Entity normalization table:**

```
canonical_entity_id    → unique ID
surface_form           → as written in text
entity_type            → PERSON, POLITICAL_PARTY, etc.
confidence             → 0.0 – 1.0
```

**Optional future enhancement:** Link to **Wikidata ID** for global entity resolution.

---

## 15. Framing Engine

The framing engine answers: **"How is the same event being presented differently?"**

It combines multiple analytical dimensions — it should **not** reduce everything into one opaque score.

### 15.1 Stance Analysis

Stance is **toward a target** (entity, policy, event):

```
Labels: SUPPORT | OPPOSE | NEUTRAL

Example:
  Target:   Government policy
  Sentence: "Opposition parties strongly criticized the policy."
  Stance:   OPPOSE
```

MuRIL should be fine-tuned on a Tamil stance dataset.

### 15.2 Sentiment Analysis

```
Labels: POSITIVE | NEGATIVE | NEUTRAL
```

Sentiment describes **tone**, not political orientation:

```
positive sentiment ≠ pro-DMK
negative sentiment ≠ anti-DMK
```

Sentiment is a **supporting feature**, not a primary bias indicator.

### 15.3 Framing Classification

Build a dedicated Tamil framing classifier using MuRIL or IndicBERT.

**Initial Frame Taxonomy:**

| Frame Label | Description |
|---|---|
| `ACHIEVEMENT` | Highlighting accomplishments |
| `CRITICISM` | Highlighting failures or shortcomings |
| `CONTROVERSY` | Emphasizing scandal or dispute |
| `ACCOUNTABILITY` | Demanding responsibility |
| `PUBLIC_WELFARE` | Focusing on people's benefit |
| `GOVERNMENT_RESPONSE` | Official reaction / defence |
| `OPPOSITION_RESPONSE` | Opposition party reaction |
| `ECONOMIC_IMPACT` | Financial consequences |
| `LAW_AND_ORDER` | Legal / crime implications |
| `IDENTITY` | Caste, religion, cultural identity |
| `CONFLICT` | Confrontation or violence |

The classifier outputs a **probability distribution**, not a single label:

```
ACHIEVEMENT:    0.72
CRITICISM:      0.14
CONTROVERSY:    0.14
```

### 15.4 Lexical Bias Analysis

Lexical models provide **interpretability** (explaining *why* framing differs), not event retrieval.

**Example log-odds output:**

| Term | Group Association Score |
|---|---|
| "சாதனை" (achievement) | +0.71 |
| "வரலாற்று" (historic) | +0.64 |
| "சர்ச்சை" (controversy) | −0.58 |
| "குற்றச்சாட்டு" (accusation) | −0.51 |

These signals are **evidence of lexical differences**, not proof of political intent.

### 15.5 Contrastive Learning for Framing

Apply **Triplet Loss contrastive learning** to train the framing model:

- Group articles by event first (anchor + positive)
- Then distinguish by editorial spin (negative)

This ensures the model learns *framing differences within the same event*, not just topic similarity.

### 15.6 Event-Level Perspective Matrix

One of the **signature product features** — aggregating per-source-group framing across an event:

```
EVENT: New Government Policy

FRAME DISTRIBUTION
                         Achievement  Criticism  Controversy
Source Group A              72%         14%         14%
Source Group B              17%         55%         28%
Source Group C              34%         29%         37%
Source Group D              18%         28%         54%

STANCE DISTRIBUTION
                         Support   Neutral   Oppose
Source Group A              0.71      0.21      0.08
Source Group B              0.12      0.24      0.64
Source Group C              0.31      0.37      0.32

COVERAGE
                         Event   Entity   Aspect
Source Group A            YES      HIGH      A
Source Group B            YES      HIGH      B
Source Group C            YES      LOW       C
Source Group D            NO       --        --
```

---

## 16. Claim Analysis Engine

Claim analysis is a **separate engine** from framing. It operates at the factual-claim level.

### 16.1 Claim Pipeline

```
Event cluster
   ↓
Extract claims from articles
   ↓
Match claims across articles (cross-source)
   ↓
Run NLI (Natural Language Inference)
   ↓
Classify: ENTAILMENT | NEUTRAL | CONTRADICTION
```

### 16.2 Claim Conflict Types

When contradictions appear, classify the nature of conflict:

| Conflict Type | Example |
|---|---|
| `NUMERIC` | "20 people injured" vs "25 people injured" |
| `DATE` | "January 5th" vs "January 7th" |
| `LOCATION` | "Chennai" vs "Coimbatore" |
| `PERSON` | Attribution to different actors |
| `EVENT_STATUS` | "approved" vs "under review" |
| `CAUSALITY` | Different claimed causes |
| `CHARACTERIZATION` | "peaceful protest" vs "violent mob" |

### 16.3 Important Distinction

NLI contradiction does **not** automatically equal political bias. A contradiction can be caused by:

- Incomplete information at publication time
- Publication timing differences
- Source reporting error
- Developing events (facts change)
- Different legitimate interpretations
- Actual political framing

Therefore contradiction is **evidence for investigation**, not an automatic bias label.

---

## 17. Blindspot Engine

### 17.1 Definition

A blindspot is defined as a **potential coverage gap** — a "Coverage Blindspot Candidate."

It is **not** defined as proven intentional suppression.

### 17.2 Three Levels of Blindspot Detection

#### Level 1 — Event Coverage

For each event, check which source groups covered it:

```
                     COVERED?
Group A              YES
Group B              YES
Group C              YES
Group D              NO       ← Event coverage gap candidate
Group E              YES
```

#### Level 2 — Entity Coverage

Within an event, check entity mention distribution:

```
Entity: Person X

Group A:   10 mentions
Group B:    2 mentions
Group C:    0 mentions   ← Entity coverage gap candidate
```

Flagged only when:
- Event confidence is high
- Enough sources exist
- Entity salience is high
- Observation window is adequate

#### Level 3 — Aspect Coverage (Most Valuable)

```
EVENT: New Government Scheme

Group A:   focuses on benefits
Group B:   focuses on cost
Group C:   focuses on opposition criticism
Group D:   focuses on implementation problems
```

All groups covered the event, but **different aspects were emphasized**. This is represented as a "Perspective / Aspect Gap" rather than a simple publication absence.

### 17.3 Mathematical Flagging

**Jaccard Similarity of Entities** defines the coverage gap:

$$\text{Jaccard}(E_A, E_B) = \frac{|E_A \cap E_B|}{|E_A \cup E_B|}$$

**Blindspot trigger rule:** Flag an entity or event as a "Blindspot" if it appears in **>80%** of articles from one bias cohort (e.g., Pro-DMK) but **<5%** of articles covering the **exact same event** from an opposing cohort (e.g., Pro-AIADMK).

### 17.4 Blindspot Ranking

```
Candidate Score = coverage_gap × entity_salience × event_significance
                  × independent_source_count × event_confidence
```

**Minimum thresholds** (preventing false blindspots):

```
minimum article count
minimum event confidence
minimum time window
minimum salience
```

### 17.5 Coverage Matrix

For each event, a coverage matrix shows source-group participation:

```
                    Source Group
Event                A    B    C    D    E
Event 1              ✓    ✓    ✓    ✓    ✓
Event 2              ✓    ✗    ✓    ✗    ✓
Event 3              ✗    ✓    ✓    ✓    ✗
```

---

## 18. Source Intelligence Layer

### 18.1 Source Orientation

Long-term publisher metadata — separate from article-level framing:

```
SOURCE ORIENTATION = Long-term publisher profile
ARTICLE FRAMING   = What this particular article does
```

A source with a known orientation **can still publish a neutral article**.

### 18.2 Publisher Prior

Publisher information is metadata and analysis context. It should **not** become the primary label that classifiers memorize.

**Avoid:** `source → label` as the only training signal.
**Instead:** Build manually reviewed article/sentence examples for stance, framing, and sentiment independently.

### 18.3 Ownership Transparency

```
source                          → outlet name
parent_company                  → corporate parent
owner                           → individual owner(s)
subsidiary_relationships        → related outlets
editorial_leadership            → editor-in-chief
reported_business_interests     → commercial connections
reported_political_affiliations → documented political links
evidence / reference            → source documentation
last_reviewed                   → date of last review
```

> **Important:** The system displays **documented relationships**. It does **not** infer "conflict of interest" simply because two entities are associated.

### 18.4 Factuality & Reliability

Do **NOT** expose a fabricated mathematical "truth score."

**Separate into:**

| Layer | Source | Data |
|---|---|---|
| **Source Reliability** | Curated historical metadata | Correction history, fact-checking record, editorial history, operational history, external monitoring |
| **Claim Verification Signal** | Calculated from event evidence | Cross-source corroboration, primary-source evidence, official/document evidence, NLI consistency, numeric consistency, later correction signals |

**User-facing representation:**

```
SOURCE RELIABILITY:     High | Medium | Low
CLAIM VERIFICATION:     Strongly corroborated | Partially corroborated
                        | Conflicting reports | Insufficient evidence
```

**Avoid:** `Truth = 87.4%` — unless a rigorously validated claim-verification system justifies such a score.

---

## 19. Event Summary Engine

The summary summarizes the **event**, not a single article.

### 19.1 Summary Pipeline

```
Event cluster
   ↓
Select high-confidence article sentences
   ↓
Remove duplicate information
   ↓
Group agreeing claims
   ↓
Identify disagreements
   ↓
Generate neutral summary
```

### 19.2 Summary Structure

```
What happened
Who is involved
What sources agree on
Where sources differ
What remains uncertain
```

### 19.3 Summarization Model

**Primary:** `mT5 / XLSum-style` multilingual summarization model
**Optional later:** Tamil-capable Llama-family model

> **Design Rule:** The LLM should sit **after** evidence extraction and comparison. The summarizer receives **structured evidence** (event facts, agreed claims, conflicting claims, entities, timeline, source articles) — not the raw news stream. This reduces hallucination risk and keeps the summary tied to retrieved evidence.

---

## 20. Database Schema

### 20.1 Conceptual Schema Overview

```
sources                → publisher metadata
source_profiles        → long-term editorial profile
ownership_entities     → corporate ownership

articles               → ingested articles
article_chunks         → chunk-level text (for future chunk NLP)

embeddings             → vector representations (pgvector)

entities               → canonical entity registry
article_entities       → article-entity associations

events                 → story clusters
event_articles         → event-article membership

article_analysis       → versioned NLP results
claims                 → extracted claims
claim_relations        → cross-source claim comparison

event_coverage         → coverage matrix data
blindspot_candidates   → detected coverage gaps

source_reliability     → reliability metadata
summaries              → event summaries
```

### 20.2 Table Definitions

#### `sources`

```
id                      UUID PK
name                    TEXT NOT NULL
domain                  TEXT
language                TEXT
orientation             TEXT        -- DRAVIDIAN_ORIENTED, AIADMK_ORIENTED, etc.
orientation_confidence  FLOAT
orientation_evidence    TEXT
last_reviewed           TIMESTAMP
created_at              TIMESTAMP
updated_at              TIMESTAMP
```

#### `source_profiles`

```
id                              UUID PK
source_id                       UUID FK → sources
historical_frame_distribution   JSONB
historical_stance_distribution  JSONB
lexical_signature               JSONB
article_count                   INTEGER
profile_period_start            TIMESTAMP
profile_period_end              TIMESTAMP
model_version                   TEXT
```

#### `ownership_entities`

```
id                              UUID PK
name                            TEXT
parent_company                  TEXT
owner                           TEXT
relationships                   JSONB
business_interests              TEXT
political_or_affiliate_links    TEXT
evidence                        TEXT
last_reviewed                   TIMESTAMP
```

#### `articles`

```
id                  UUID PK
source_id           UUID FK → sources
url                 TEXT NOT NULL
canonical_url       TEXT
title               TEXT
description         TEXT
body                TEXT
language            TEXT
author              TEXT
published_at        TIMESTAMP
collected_at        TIMESTAMP
content_hash        TEXT    -- SHA-256
status              TEXT    -- queued / processed / failed
raw_payload         JSONB
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

#### `article_chunks`

```
id              UUID PK
article_id      UUID FK → articles
chunk_index     INTEGER
text            TEXT
start_offset    INTEGER
end_offset      INTEGER
created_at      TIMESTAMP
```

#### `embeddings`

```
id              UUID PK
article_id      UUID FK → articles
chunk_id        UUID FK → article_chunks (nullable)
embedding_type  TEXT    -- TITLE / LEAD / CHUNK / ARTICLE
model_name      TEXT
model_version   TEXT
vector          VECTOR(D)   -- pgvector, dimension matches model
created_at      TIMESTAMP
```

#### `entities`

```
id              UUID PK
canonical_name  TEXT NOT NULL
entity_type     TEXT    -- PERSON, POLITICAL_PARTY, etc.
wikidata_id     TEXT    -- optional
aliases         JSONB   -- list of known surface forms
```

#### `article_entities`

```
article_id      UUID FK → articles
entity_id       UUID FK → entities
surface_form    TEXT
confidence      FLOAT
salience        FLOAT
position        INTEGER
```

#### `events`

```
id                      UUID PK
representative_title    TEXT
summary                 TEXT
first_seen              TIMESTAMP
last_updated            TIMESTAMP
status                  TEXT
cluster_confidence      FLOAT
centroid_embedding      VECTOR(D)
```

#### `event_articles`

```
event_id                UUID FK → events
article_id              UUID FK → articles
similarity              FLOAT
assignment_confidence   FLOAT
assignment_method       TEXT    -- graph_clustering / threshold / manual
```

#### `article_analysis`

```
id                  UUID PK
article_id          UUID FK → articles
model_version       TEXT
stance              TEXT
stance_confidence   FLOAT
sentiment           TEXT
sentiment_confidence FLOAT
frame_distribution  JSONB
lexical_signature   JSONB
created_at          TIMESTAMP
```

#### `claims`

```
id              UUID PK
event_id        UUID FK → events
article_id      UUID FK → articles
claim_text      TEXT
claim_type      TEXT
confidence      FLOAT
created_at      TIMESTAMP
```

#### `claim_relations`

```
claim_a         UUID FK → claims
claim_b         UUID FK → claims
relation        TEXT    -- ENTAILMENT / NEUTRAL / CONTRADICTION
conflict_type   TEXT    -- NUMERIC / DATE / LOCATION / etc.
confidence      FLOAT
```

#### `event_coverage`

```
event_id        UUID FK → events
source_id       UUID FK → sources
source_group    TEXT
coverage_type   TEXT
mention_count   INTEGER
entity_coverage JSONB
aspect_coverage JSONB
last_seen       TIMESTAMP
```

#### `blindspot_candidates`

```
id              UUID PK
event_id        UUID FK → events
source_group    TEXT
blindspot_type  TEXT    -- EVENT / ENTITY / ASPECT
score           FLOAT
evidence        JSONB
status          TEXT    -- candidate / confirmed / dismissed
created_at      TIMESTAMP
```

#### `source_reliability`

```
id                      UUID PK
source_id               UUID FK → sources
reliability_level       TEXT    -- High / Medium / Low
historical_notes        TEXT
correction_history      JSONB
fact_checking_history   JSONB
evidence                TEXT
last_reviewed           TIMESTAMP
```

#### `summaries`

```
id                      UUID PK
event_id                UUID FK → events
summary                 TEXT
summary_type            TEXT
model_name              TEXT
model_version           TEXT
evidence_article_count  INTEGER
created_at              TIMESTAMP
updated_at              TIMESTAMP
```

---

## 21. API Architecture

FastAPI exposes REST endpoints organized by resource domain.

### 21.1 Articles

```http
GET  /articles                          → list articles (paginated)
GET  /articles/{article_id}             → article detail + analysis

Filters: source, event, date, language, orientation
```

### 21.2 Events

```http
GET  /events                            → list events (paginated)
GET  /events/{event_id}                 → event detail
GET  /events/{event_id}/timeline        → chronological article list
```

### 21.3 Event Analysis

```http
GET  /events/{event_id}/framing         → perspective matrix
GET  /events/{event_id}/claims          → claim agreement / conflict
GET  /events/{event_id}/coverage        → coverage matrix
GET  /events/{event_id}/blindspots      → blindspot candidates
```

### 21.4 Blindspots

```http
GET  /blindspots                        → global blindspot feed
```

### 21.5 Sources

```http
GET  /sources                           → list all sources
GET  /sources/{source_id}               → source detail
GET  /sources/{source_id}/profile       → editorial profile
GET  /sources/{source_id}/transparency  → ownership & reliability
```

### 21.6 Search

```http
GET  /search?q=                         → hybrid keyword + semantic search
```

### 21.7 Administration

```http
POST /admin/ingest/trigger              → manually trigger ingestion
```

---

## 22. Frontend Architecture

### 22.1 Technology

**React / Next.js** — modern component-based frontend framework.

### 22.2 Five Primary Screens

#### Screen 1: Home / Event Feed

Displays latest events with:

```
Event title
Article count
Source count
Coverage breadth indicator
Last updated timestamp
```

#### Screen 2: Event Timeline

The **core product screen**:

```
┌──────────────────────────────────────────────────┐
│  EVENT TITLE                                     │
│  Updated: ...      Sources: ...                  │
├──────────────────────────────────────────────────┤
│  EVENT SUMMARY                                   │
│  (neutral, evidence-grounded)                    │
├──────────────────────────────────────────────────┤
│  TIMELINE                                        │
│  10:00  Source A  →  headline + snippet          │
│  11:15  Source B  →  headline + snippet          │
│  12:30  Source C  →  headline + snippet          │
│  14:10  Source D  →  headline + snippet          │
├──────────────────────────────────────────────────┤
│  PERSPECTIVE MATRIX                              │
│  (frame distribution, stance distribution)       │
├──────────────────────────────────────────────────┤
│  CLAIM AGREEMENT / CONFLICT                      │
│  (agreed claims, contradictions, conflict types) │
├──────────────────────────────────────────────────┤
│  COVERAGE BLINDSPOTS                             │
│  (missing source groups, entity/aspect gaps)     │
├──────────────────────────────────────────────────┤
│  SOURCE & OWNERSHIP INFORMATION                  │
│  (orientation, ownership, reliability)           │
└──────────────────────────────────────────────────┘
```

#### Screen 3: Perspective Matrix

Full-screen matrix view:

```
Source groups × Framing + Stance + Sentiment + Coverage
```

#### Screen 4: Blindspot Feed

Global blindspot stream:

```
Event | Missing group | Blindspot type | Evidence | Confidence
```

#### Screen 5: Source Profile

Per-publisher deep dive:

```
Orientation + Historical framing + Ownership + Reliability metadata + Coverage patterns
```

---

## 23. Search Architecture

Search combines four retrieval methods:

```
Keyword search (PostgreSQL full-text)
  +
Semantic vector search (pgvector cosine similarity)
  +
Entity search (NER entity matching)
  +
Event search (story cluster matching)
```

Example query: `"ஸ்டாலின் கல்வித் திட்டம்"` retrieves:
- Matching keywords
- Semantically related articles
- Events mentioning the entities
- Historical events on the same topic

---

## 24. Async Processing & Queuing

### 24.1 Stack

```
Redis (message broker) + Celery (task workers)
```

### 24.2 Task Queues

| Queue | Purpose |
|---|---|
| `ingest_queue` | New article ingestion |
| `embedding_queue` | Generate sentence embeddings |
| `ner_queue` | Named entity recognition |
| `classification_queue` | Stance, sentiment, framing classification |
| `analysis_queue` | Event resolution, clustering, coverage |
| `summary_queue` | Event summary generation |

---

## 25. Complete Processing Flow

The end-to-end flow for every article, numbered step-by-step:

```
 1. API source returns article
 2. Ingestion worker validates it
 3. Language detector checks Tamil
 4. Article is normalized (Unicode NFC, boilerplate removal)
 5. Duplicate detector checks URL / content hash
 6. Article is stored in PostgreSQL
 7. NLP job enters Redis queue
 8. Embedding generated (Tamil SBERT)
 9. NER generated (IndicNER)
10. Entity normalization performed (surface form → canonical)
11. Candidate events retrieved from pgvector (top-k nearest neighbors)
12. Event similarity calculated (composite formula)
13. Article attached to existing event OR new event created
14. Stance generated (MuRIL fine-tuned)
15. Sentiment generated (MuRIL fine-tuned)
16. Frame classification generated (MuRIL/IndicBERT)
17. Lexical analysis generated (TF-IDF + log-odds)
18. Claims extracted
19. Cross-source claim comparison performed (NLI)
20. Event coverage matrix updated
21. Blindspot candidates recalculated
22. Event summary updated (mT5/XLSum)
23. FastAPI exposes the updated event via REST
24. Frontend displays the perspective matrix and timeline
```

---

## 26. Model Versioning & Caching

### 26.1 Model Versioning

Every NLP result must know which model generated it:

```
embedding_model:   l3cube-pune/tamil-sentence-similarity-sbert
embedding_version: v1
stance_model:      muril-tamil-stance-v2
ner_model:         indicner-tamil-news-v2
```

This is essential for reproducibility and when models are retrained.

### 26.2 Caching Strategy

| Cached Data | Storage | TTL |
|---|---|---|
| Article NLP results | Redis + PostgreSQL | Persistent |
| Embeddings | pgvector (PostgreSQL) | Persistent |
| Event similarity queries | Redis | Short-lived |
| Source profiles | Redis | Medium-lived |
| Event summaries | Redis + PostgreSQL | Until event update |

Redis handles short-lived cache data. PostgreSQL remains the persistent source of truth.

---

## 27. Security

### 27.1 API Key Management

Store all secrets in **environment variables**:

```
NEWS_DATA_API_KEY
CURRENTS_API_KEY
DATABASE_URL
REDIS_URL
```

**Never put keys into:** Git, Docker image, frontend code, source code.

**Use:**

```
.env                → local development
.env.example        → template (committed to git)
Docker secrets      → production (later)
```

### 27.2 Rate Limiting

The ingestion worker enforces **per-provider rate limits**:

```
Google News  → provider-specific schedule
NewsData     → provider-specific schedule
Currents     → provider-specific schedule
```

Do not continuously poll every provider. Use staggered CRON schedules.

---

## 28. Repository Structure

```
perspective_lens/
│
├── docker-compose.yml
├── .env.example
├── README.md
├── ARCHITECTURE.md
│
├── services/
│   │
│   ├── ingestion/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py           ← abstract NewsProvider
│   │   │   │   ├── google_news.py
│   │   │   │   ├── newsdata.py
│   │   │   │   └── currents.py
│   │   │   ├── normalization/
│   │   │   │   ├── unicode.py
│   │   │   │   └── boilerplate.py
│   │   │   ├── deduplication/
│   │   │   │   ├── url_hash.py
│   │   │   │   ├── content_hash.py
│   │   │   │   └── near_duplicate.py
│   │   │   └── tasks/
│   │   │       └── celery_tasks.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── nlp-engine/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models/
│   │   │   │   └── model_registry.py
│   │   │   ├── embedding/
│   │   │   │   └── sbert.py
│   │   │   ├── ner/
│   │   │   │   ├── indicner.py
│   │   │   │   └── entity_normalizer.py
│   │   │   ├── stance/
│   │   │   │   └── muril_stance.py
│   │   │   ├── sentiment/
│   │   │   │   └── muril_sentiment.py
│   │   │   └── framing/
│   │   │       └── frame_classifier.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── analysis-worker/
│   │   ├── app/
│   │   │   ├── event_resolution/
│   │   │   │   ├── similarity.py
│   │   │   │   └── assignment.py
│   │   │   ├── clustering/
│   │   │   │   ├── graph_clustering.py
│   │   │   │   └── hdbscan_experimental.py
│   │   │   ├── claims/
│   │   │   │   ├── extraction.py
│   │   │   │   └── nli_comparison.py
│   │   │   ├── lexical/
│   │   │   │   ├── tfidf.py
│   │   │   │   └── log_odds.py
│   │   │   ├── coverage/
│   │   │   │   └── coverage_matrix.py
│   │   │   └── blindspots/
│   │   │       ├── detection.py
│   │   │       └── ranking.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── routes/
│       │   │   ├── articles.py
│       │   │   ├── events.py
│       │   │   ├── blindspots.py
│       │   │   ├── sources.py
│       │   │   └── search.py
│       │   ├── schemas/
│       │   │   ├── article.py
│       │   │   ├── event.py
│       │   │   ├── source.py
│       │   │   └── blindspot.py
│       │   ├── services/
│       │   │   ├── article_service.py
│       │   │   ├── event_service.py
│       │   │   └── search_service.py
│       │   └── dependencies/
│       │       ├── database.py
│       │       └── auth.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── styles/
│   ├── Dockerfile
│   └── package.json
│
├── database/
│   ├── migrations/
│   ├── schema.sql
│   └── seed/
│
├── models/
│   └── README.md
│
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── annotations/
│
├── experiments/
│   ├── clustering/
│   ├── stance/
│   ├── framing/
│   └── ner/
│
├── scripts/
│
├── prompt/
│   ├── base_prompt.txt
│   ├── perslens-gemini-architecture.md
│   └── perslens-gpt-architecture.md
│
└── docs/
    ├── architecture.md
    ├── data-model.md
    ├── api.md
    └── model-card.md
```

---

## 29. Training Data Strategy

### 29.1 Tamil Annotation Dataset

The project should create its own small Tamil annotation dataset:

```
event_id
article_id
sentence
target_entity
stance           → SUPPORT / OPPOSE / NEUTRAL
sentiment        → POSITIVE / NEGATIVE / NEUTRAL
frame            → ACHIEVEMENT / CRITICISM / etc.
claim            → extracted claim text
claim_relation   → ENTAILMENT / NEUTRAL / CONTRADICTION
```

### 29.2 Event Annotation Dataset

For clustering evaluation, create article pairs:

```
article_A
article_B
same_event = YES / NO
```

This allows tuning:
- Semantic threshold
- Entity weight
- Temporal weight
- Clustering method selection

### 29.3 Stance Labels

```
SUPPORT | OPPOSE | NEUTRAL

Example:
  Event:    new government policy
  Sentence: "Opposition parties welcomed the policy."
  Target:   government policy
  Stance:   SUPPORT
```

### 29.4 Framing Labels

Initial taxonomy (may evolve after annotation):

```
ACHIEVEMENT | CRITICISM | CONTROVERSY | ACCOUNTABILITY
PUBLIC_WELFARE | GOVERNMENT_RESPONSE | OPPOSITION_RESPONSE
ECONOMIC_IMPACT | LAW_AND_ORDER | IDENTITY | CONFLICT
```

---

## 30. Evaluation Framework

The platform must be evaluated **component by component**.

### 30.1 Metrics by Component

| Component | Metrics |
|---|---|
| **Event Resolution** | Precision, Recall, F1, Adjusted Rand Index |
| **NER** | Precision, Recall, F1 (per entity type) |
| **Stance** | Macro F1, Per-class F1, Confusion matrix |
| **Framing** | Macro F1, Per-class F1 |
| **Sentiment** | Accuracy, Macro F1 |
| **Blindspot Detection** | Precision, Recall, F1 (against manually reviewed events) |
| **Claim Analysis** | NLI accuracy, Macro F1 |
| **Summarization** | ROUGE-1, ROUGE-2, ROUGE-L + manual factual consistency |

### 30.2 Critical Evaluation Rule

A high classifier accuracy is **not sufficient**. For example, `92% bias accuracy` is meaningless if the classifier learned `Sun News → Pro-DMK` from the source name.

**Required evaluation strategies:**

- **Publisher-stratified splits** — train/test split ensuring the model cannot memorize source → label
- **Cross-source testing** — test whether the model actually learned framing patterns independent of publisher identity

---

## 31. Research Experiments

### Experiment 1: Embedding Model Comparison

```
L3Cube Tamil SBERT  vs  Indic multilingual SBERT  vs  BGE-M3
```

Evaluate on event clustering quality.

### Experiment 2: Event Resolution Signals

```
Semantic-only  vs  Semantic + NER  vs  Semantic + NER + Temporal
```

Evaluate which combination produces the best event clusters.

### Experiment 3: Perspective Distinguishing

```
Sentiment-only  vs  Stance-only  vs  Stance + Sentiment + Framing
```

For distinguishing editorial perspectives within the same event.

### Experiment 4: Lexical Interpretability

```
TF-IDF  vs  TF-IDF + Character N-grams  vs  Log-odds
```

For explainable lexical framing patterns.

---

## 32. Technology Stack Summary

### Backend

```
Python, FastAPI, Pydantic, SQLAlchemy, Celery, Redis
```

### Database

```
PostgreSQL, pgvector, JSONB
```

### NLP Models

```
fastText lid.176                               → Language detection
l3cube-pune/tamil-sentence-similarity-sbert    → Sentence embeddings
ai4bharat/IndicNER                             → Named entity recognition
google/muril-base-cased                        → Stance, sentiment (fine-tuned)
ai4bharat/IndicBERTv2-MLM-Sam-TLM             → Classification backbone
IndicBERT/MuRIL NLI model                     → Claim analysis
csebuetnlp/mT5_multilingual_XLSum             → Summarization
```

### NLP Utilities

```
scikit-learn, sentence-transformers, transformers, PyTorch
networkx, Leiden/Louvain library, HDBSCAN
```

### Frontend

```
React / Next.js
```

### Infrastructure

```
Docker, Docker Compose
Nginx (optional)
MinIO (optional)
```

---

## 33. Development Phases

### Phase 0 — Foundation

```
Docker Compose + PostgreSQL + pgvector + Redis + FastAPI + basic schema
```

**Deliverable:** Backend boots successfully.

---

### Phase 1 — Ingestion

```
Google News + NewsData.io + Currents API + normalization + deduplication + storage
```

**Deliverable:** Tamil articles automatically enter the database.

---

### Phase 2 — Event Discovery

```
Tamil SBERT + pgvector + nearest-neighbor retrieval + graph clustering + event timelines
```

**Deliverable:** Articles are automatically grouped into stories.

---

### Phase 3 — Tamil NLP

```
IndicNER + stance + sentiment + framing + lexical analysis
```

**Deliverable:** Each article has a structured framing profile.

---

### Phase 4 — Cross-Source Analysis

```
Claim extraction + NLI + contradiction detection + source comparison
```

**Deliverable:** The system identifies agreement and disagreement.

---

### Phase 5 — Blindspots

```
Event coverage + entity coverage + aspect coverage + blindspot ranking
```

**Deliverable:** Coverage blindspot feed.

---

### Phase 6 — Source Intelligence

```
Orientation metadata + ownership transparency + reliability metadata
```

**Deliverable:** Transparent publisher profiles.

---

### Phase 7 — Summarization

```
Event-grounded Tamil summary (mT5/XLSum)
```

**Deliverable:** Neutral event digest.

---

### Phase 8 — Product Hardening

```
Caching + rate-limit handling + model versioning + logging + monitoring + tests + evaluation
```

**Deliverable:** Production-ready platform.

---

## 34. Ethical Guardrails

### What the System Should NOT Claim

| ❌ Avoid | ✅ Use Instead |
|---|---|
| "This article is objectively biased." | "Framing differs from other reports." |
| "This outlet is lying." | "Reports contain conflicting claims." |
| "This outlet intentionally suppressed this event." | "Coverage gap detected." |
| "This claim is 87% true." | "Claim verification: Conflicting reports." |
| "This article is pro-DMK because the model says so." | "Source orientation: [label], based on [evidence]." |

This protects both the **technical credibility** and the **integrity** of the product.

### Research Contribution Framing

Present the project as:

> **"An event-centric Tamil news intelligence architecture for multi-source semantic aggregation, media-framing comparison, claim-level disagreement analysis, and coverage-blindspot detection."**

**Key research contributions:**

1. Tamil event resolution across multiple publishers
2. Multi-dimensional framing analysis (stance + sentiment + frame + lexical)
3. Source-independent story clustering (graph-based, not publisher-dependent)
4. Claim agreement/contradiction analysis (NLI-based)
5. Event/entity/aspect-level coverage gap detection
6. Explainable lexical framing analysis (log-odds)
7. Transparent source orientation and ownership layer
8. A domain-specific Tamil news annotation dataset

### Anti-Patterns to Avoid

```
❌  K-Means as primary event clustering (unknown cluster count)
❌  Publisher label → article label training (source memorization)
❌  NER-only blindspot detection (insufficient signal)
❌  Sentiment-only bias detection (tone ≠ political bias)
❌  LLM-first bias classification (should be evidence-last)
❌  Fabricated mathematical factuality score
❌  Many independent NLP containers (start with one)
❌  10+ microservices, Kubernetes, Kafka in MVP
```

---

*Last updated: 2026-08-15*
*Synthesized from Gemini and GPT architecture specifications.*
