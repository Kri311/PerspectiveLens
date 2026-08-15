# PerspectiveLens — Phase-Wise Implementation Plan

> **Building a "Ground News for Tamil Nadu" — step by step, learning as we go.**

---

## How This Plan Is Structured

Each phase is designed around three principles:

1. **Learn** — Understand the concepts and tools before writing code
2. **Build** — Implement with a clear, testable deliverable
3. **Verify** — Confirm it works before moving on

Every phase ends with a **working checkpoint** — you'll never have a broken system between phases.

---

## Ground News ↔ PerspectiveLens Feature Mapping

Before we start, here's how our features map to Ground News (our inspiration):

| Ground News Feature | PerspectiveLens Equivalent | Phase |
|---|---|---|
| Story clustering (60K articles/day merged by event) | Event Resolution + Graph Clustering (Tamil SBERT + pgvector) | Phase 2 |
| Bias Bar (Left / Center / Right distribution) | **Orientation Bar** (Dravidian / AIADMK / Conservative / Populist distribution) | Phase 3 |
| Bias ratings from AllSides, Ad Fontes, MBFC | Source orientation from Tamil media-monitoring metadata (curated, not third-party) | Phase 5 |
| Factuality ratings | Source reliability metadata (correction history, editorial history) | Phase 5 |
| Blindspot feed | **Blindspot Engine** (event, entity, and aspect-level coverage gaps) | Phase 4 |
| Ownership transparency | **Ownership layer** (corporate ownership, political affiliations) | Phase 5 |
| Source comparison on story page | **Perspective Matrix** (stance × framing × sentiment per source group) | Phase 3 |
| AI-generated story summary | **Event Summary Engine** (evidence-grounded mT5 Tamil summary) | Phase 6 |
| Search (keyword + URL) | **Hybrid Search** (keyword + semantic + entity + event) | Phase 7 |
| Frontend (story page, blindspot feed, source profiles) | **5-screen frontend** (Event Feed, Timeline, Matrix, Blindspot, Source Profile) | Phase 7 |

> **Key difference:** Ground News uses 3 third-party bias-rating organizations. We use NLP models (MuRIL, IndicNER, SBERT) to **computationally detect** framing differences, plus curated source metadata. This is what makes PerspectiveLens a research contribution, not just an aggregator.

---

## Phase 0 — Foundation & Infrastructure

### 🎓 What You'll Learn
- Docker & Docker Compose fundamentals — containerizing services
- PostgreSQL + pgvector — relational database with vector math
- Redis — message broker for async processing
- FastAPI — modern Python API framework
- Project structure conventions for microservices

### 🔨 What We'll Build

| Component | Details |
|---|---|
| `docker-compose.yml` | Orchestrates all 7 containers |
| `postgres` container | PostgreSQL 16 + pgvector extension + initial schema |
| `redis` container | Redis 7 for message broker + cache |
| `api` container | FastAPI skeleton with health check endpoint |
| Database schema | Core tables: `sources`, `articles`, `events`, `embeddings` |
| `.env.example` | Environment variable template |
| Project structure | Full `services/` directory layout |

### 📂 Files Created

```
perspective_lens/
├── docker-compose.yml
├── .env.example
├── .env                          (gitignored)
├── .dockerignore
├── .gitignore
│
├── database/
│   ├── schema.sql                (full DDL with pgvector)
│   └── seed/
│       └── sources.sql           (Tamil news source metadata)
│
└── services/
    └── api/
        ├── Dockerfile
        ├── requirements.txt
        └── app/
            ├── main.py           (FastAPI app with /health)
            ├── dependencies/
            │   └── database.py   (SQLAlchemy + async session)
            └── routes/
                └── health.py
```

### ✅ Deliverable
```
$ docker compose up
→ PostgreSQL boots with schema + pgvector
→ Redis boots
→ FastAPI boots and returns {"status": "ok"} on GET /health
→ Tables are created and seeded with Tamil news source metadata
```

### 📝 Learning Checkpoint
> At this point you'll understand: How Docker Compose wires multiple services together, how pgvector extends PostgreSQL for vector math, and why FastAPI is our choice for Python APIs.

---

## Phase 1 — Data Ingestion

### 🎓 What You'll Learn
- News API integration patterns (REST APIs, RSS feeds)
- Provider abstraction pattern — making the system source-agnostic
- Text preprocessing for Tamil — Unicode NFC normalization
- Deduplication strategies (URL hash, content hash, near-duplicate)
- Language detection with fastText
- Celery + Redis for background task processing
- Rate limiting per provider

### 🔨 What We'll Build

| Component | Details |
|---|---|
| `ingestion-worker` container | Celery worker that fetches from news APIs |
| Provider abstraction | `NewsProvider` base class + implementations for Google News, NewsData.io, Currents API |
| Preprocessing pipeline | Unicode normalization → boilerplate removal → language detection → deduplication |
| Celery tasks | Scheduled CRON fetching jobs per provider |

### 📂 Files Created

```
services/ingestion/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py
    ├── providers/
    │   ├── __init__.py
    │   ├── base.py               (abstract NewsProvider)
    │   ├── google_news.py
    │   ├── newsdata.py
    │   └── currents.py
    ├── normalization/
    │   ├── unicode.py            (NFC normalization)
    │   └── boilerplate.py        (trafilatura-based cleaning)
    ├── deduplication/
    │   ├── url_hash.py
    │   ├── content_hash.py
    │   └── language_filter.py    (fastText lid.176)
    └── tasks/
        └── celery_tasks.py       (scheduled ingestion)
```

### ✅ Deliverable
```
$ docker compose up
→ Ingestion worker connects to news APIs
→ Tamil articles are automatically fetched, cleaned, deduplicated
→ Articles appear in the PostgreSQL `articles` table
→ Non-Tamil articles are rejected
→ Duplicate articles are detected and skipped
```

### 📝 Learning Checkpoint
> You'll understand: How news APIs work, why Unicode normalization matters for Tamil, how fastText detects language, and how Celery manages background jobs.

---

## Phase 2 — Event Discovery & Story Clustering

### 🎓 What You'll Learn
- Sentence embeddings — how SBERT converts text to dense vectors
- Tamil-specific NLP — why `l3cube-pune/tamil-sentence-similarity-sbert` works for Tamil
- Vector similarity search — cosine similarity via pgvector
- Event resolution — composite similarity (semantic + entity + temporal)
- Graph-based clustering — kNN graph → Leiden/Louvain community detection
- Why graph clustering beats K-Means for news (unknown cluster count, transitive chains)
- Named Entity Recognition — IndicNER for Tamil entities (PERSON, POLITICAL_PARTY, LOCATION, etc.)

### 🔨 What We'll Build

| Component | Details |
|---|---|
| `nlp-engine` container | GPU-capable service hosting SBERT + IndicNER |
| Embedding pipeline | Article → title + lead → Tamil SBERT → vector → pgvector |
| NER pipeline | Article → IndicNER → entities → normalization → storage |
| Event resolution | New article → pgvector top-k → composite similarity → assign/create event |
| Story clustering | kNN graph → Leiden community detection → story clusters |
| `analysis-worker` container | Runs event resolution + clustering as background tasks |

### Key Concepts Explained During Build

**Composite Event Similarity Formula:**

$$\text{EventSimilarity} = 0.55 \times \text{Semantic} + 0.20 \times \text{Entity} + 0.10 \times \text{Temporal} + 0.10 \times \text{Keyword} + 0.05 \times \text{Location}$$

**Why this matters:** Two articles about "Government launches a new scheme" and "CM announces welfare plan" have different words but describe the **same event**. Embeddings catch the semantic similarity; NER catches shared entities; temporal signals catch the timing.

### 📂 Files Created

```
services/nlp-engine/
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py                   (FastAPI with /embed, /ner endpoints)
    ├── embedding/
    │   └── sbert.py              (Tamil SBERT wrapper)
    ├── ner/
    │   ├── indicner.py           (IndicNER wrapper)
    │   └── entity_normalizer.py  (surface form → canonical)
    └── models/
        └── model_registry.py     (lazy model loading + versioning)

services/analysis-worker/
├── Dockerfile
├── requirements.txt
└── app/
    ├── event_resolution/
    │   ├── similarity.py         (composite similarity calc)
    │   └── assignment.py         (threshold-based event assignment)
    └── clustering/
        ├── graph_clustering.py   (kNN → Leiden/Louvain)
        └── hdbscan_experimental.py
```

### ✅ Deliverable
```
→ New articles automatically get embeddings and NER
→ Articles about the same event are grouped into story clusters
→ Each story cluster has a timeline (articles sorted by published_at)
→ API endpoint: GET /events returns story clusters
→ API endpoint: GET /events/{id}/timeline returns chronological articles
```

### 📝 Learning Checkpoint
> You'll understand: How sentence embeddings work, why cosine similarity finds "same event, different words", how NER extracts Tamil entities, and how graph clustering handles evolving news stories.

---

## Phase 3 — Framing Analysis & Perspective Matrix

### 🎓 What You'll Learn
- Stance analysis — Support / Oppose / Neutral toward a target (MuRIL fine-tuned)
- Sentiment analysis — tone detection (Positive / Negative / Neutral)
- Framing classification — how the same event gets "spun" differently (11 frame categories)
- Lexical bias — log-odds ratio to surface loaded words unique to each source group
- Contrastive learning — Triplet Loss for learning framing differences within events
- **The Perspective Matrix** — Ground News's core innovation, adapted for Tamil Nadu

### 🔨 What We'll Build

| Component | Details |
|---|---|
| Stance classifier | MuRIL fine-tuned → SUPPORT / OPPOSE / NEUTRAL per target entity |
| Sentiment classifier | MuRIL fine-tuned → POSITIVE / NEGATIVE / NEUTRAL |
| Framing classifier | MuRIL/IndicBERT → 11 frame categories with probability distributions |
| Lexical bias engine | TF-IDF + character n-grams + log-odds ratio |
| Perspective Matrix API | Per-event aggregation of stance × framing × sentiment by source group |
| Orientation Bar | Visual distribution of coverage across orientation groups (like Ground News's Bias Bar) |

### Key Concepts Explained During Build

**Ground News Analogy:** When you click a story on Ground News, you see a "Bias Bar" showing what % of Left, Center, Right outlets covered it. Our **Orientation Bar** does the same but with Tamil Nadu's political spectrum:

```
Event: New Government Policy

Coverage:  ████████░░  ██████████  ████░░░░░░  ██████░░░░
          Dravidian    AIADMK      Conservative  Populist
           (80%)       (100%)        (40%)        (60%)
```

**The Perspective Matrix** goes deeper — showing frame and stance distributions:

```
                     Achievement  Criticism  Controversy
Dravidian-oriented      72%         14%         14%
AIADMK-oriented         17%         55%         28%
Conservative            34%         29%         37%
```

### 📂 Files Created

```
services/nlp-engine/app/
├── stance/
│   └── muril_stance.py
├── sentiment/
│   └── muril_sentiment.py
└── framing/
    └── frame_classifier.py

services/analysis-worker/app/
└── lexical/
    ├── tfidf.py
    └── log_odds.py

services/api/app/routes/
├── events.py                     (updated with framing endpoints)
└── schemas/
    └── event.py                  (Perspective Matrix response schema)
```

### ✅ Deliverable
```
→ Every article gets stance, sentiment, and framing analysis
→ API: GET /events/{id}/framing returns the full Perspective Matrix
→ Lexical bias words are extracted per source group per event
→ The Orientation Bar shows coverage distribution across groups
```

### 📝 Learning Checkpoint
> You'll understand: The difference between stance, sentiment, and framing (they're NOT the same thing), how log-odds isolates editorial word choices, and why the Perspective Matrix is more useful than a single "bias score."

---

## Phase 4 — Blindspot & Claim Analysis

### 🎓 What You'll Learn
- Blindspot detection at three levels (event, entity, aspect) — Ground News's signature feature
- Coverage matrix — which source groups covered which events
- Jaccard similarity for entity coverage gaps
- Natural Language Inference (NLI) — detecting agreement/contradiction between claims
- Claim conflict classification (NUMERIC, DATE, PERSON, CAUSALITY, etc.)
- Why "contradiction ≠ bias" — the nuance of responsible analysis

### 🔨 What We'll Build

| Component | Details |
|---|---|
| Coverage matrix | Per-event × per-source-group presence/absence tracking |
| Blindspot Level 1 | Event coverage gaps — "Group D didn't cover this at all" |
| Blindspot Level 2 | Entity coverage gaps — "Group C never mentions Person X" |
| Blindspot Level 3 | Aspect coverage gaps — "Group A focuses on benefits, Group B on cost" |
| Blindspot ranking | Score = coverage_gap × entity_salience × event_significance × source_count |
| Claim extraction | Extract factual claims from event cluster articles |
| NLI engine | IndicBERT/MuRIL NLI → ENTAILMENT / NEUTRAL / CONTRADICTION |
| Conflict classifier | Categorize contradictions (NUMERIC, DATE, LOCATION, etc.) |

### Key Concepts Explained During Build

**Ground News Analogy:** Ground News's Blindspot feed shows "Stories disproportionately covered by one side of the political spectrum." Ours does the same but goes deeper:

| Ground News Blindspot | PerspectiveLens Blindspot |
|---|---|
| "Right-leaning media covered this, Left didn't" | **Level 1:** "AIADMK-oriented outlets covered this, Dravidian outlets didn't" |
| (not available) | **Level 2:** "Person X mentioned 10 times by Group A, 0 times by Group C" |
| (not available) | **Level 3:** "All groups covered it, but Group A focused on benefits while Group B focused on cost" |

**The blindspot trigger rule:**
> Flag as blindspot if entity appears in **>80%** of articles from one cohort but **<5%** from the opposing cohort covering the **same event**.

### 📂 Files Created

```
services/analysis-worker/app/
├── coverage/
│   └── coverage_matrix.py
├── blindspots/
│   ├── detection.py              (3-level blindspot detection)
│   └── ranking.py                (significance scoring)
└── claims/
    ├── extraction.py             (claim extraction from articles)
    └── nli_comparison.py         (cross-source NLI)

services/api/app/routes/
├── blindspots.py                 (Blindspot Feed API)
└── events.py                     (updated: /events/{id}/claims, /coverage, /blindspots)
```

### ✅ Deliverable
```
→ API: GET /blindspots returns the global blindspot feed
→ API: GET /events/{id}/blindspots returns event-specific gaps
→ API: GET /events/{id}/claims returns claim agreement/contradiction
→ API: GET /events/{id}/coverage returns the coverage matrix
→ Blindspots are ranked by significance score
→ Claim conflicts are categorized by type
```

### 📝 Learning Checkpoint
> You'll understand: How coverage gaps are mathematically detected, why NLI contradiction doesn't mean "this source is lying", and how aspect-level blindspots reveal the most interesting editorial choices.

---

## Phase 5 — Source Intelligence & Metadata

### 🎓 What You'll Learn
- Source orientation as metadata (not prediction) — a key design decision
- Ownership transparency — why "who owns the news" matters
- Source reliability vs. factuality scores — why we don't generate fake "truth percentages"
- Historical editorial profiling — tracking how a source's framing evolves over time
- The distinction between article framing and source orientation

### 🔨 What We'll Build

| Component | Details |
|---|---|
| Source profiles | Long-term editorial profile per publisher (historical frame/stance distribution) |
| Ownership layer | Corporate ownership, political affiliations, subsidiary relationships |
| Reliability metadata | Correction history, fact-checking record, editorial history |
| Source orientation API | Transparent, reviewable, evidence-backed orientation labels |

### Key Concepts Explained During Build

**Ground News Analogy:** Ground News shows three things per source: **Bias** (political leaning), **Factuality** (reporting reliability), and **Ownership** (corporate parent). We do the same but localized:

| Ground News | PerspectiveLens |
|---|---|
| Bias: "Lean Left" | Orientation: "DRAVIDIAN_ORIENTED" (confidence: 0.85, evidence: "external media-monitoring reference") |
| Factuality: "High" | Reliability: "Medium" (based on correction history, not a fake score) |
| Ownership: "Owned by X Corp" | Ownership: parent company + owner + political affiliations + evidence + last reviewed |

### 📂 Files Created

```
services/api/app/routes/
└── sources.py                    (Source Profile, Ownership, Reliability APIs)

database/seed/
├── sources.sql                   (updated with full orientation metadata)
├── ownership.sql                 (ownership entities for Tamil publishers)
└── reliability.sql               (reliability metadata)
```

### ✅ Deliverable
```
→ API: GET /sources returns all sources with orientation
→ API: GET /sources/{id}/profile returns historical editorial profile
→ API: GET /sources/{id}/transparency returns ownership + reliability
→ Source profiles auto-update as more articles are analyzed
```

### 📝 Learning Checkpoint
> You'll understand: Why source orientation is metadata (not a model prediction), why "Truth = 87.4%" is dangerous, and how to present publisher information transparently without making accusatory claims.

---

## Phase 6 — Event Summarization

### 🎓 What You'll Learn
- Multilingual abstractive summarization with mT5/XLSum
- Evidence-grounded generation — why the summarizer receives structured evidence, not raw text
- Hallucination prevention — keeping summaries tied to retrieved evidence
- Neutral event summaries — summarizing events, not individual articles

### 🔨 What We'll Build

| Component | Details |
|---|---|
| Summary pipeline | Event cluster → select high-confidence sentences → deduplicate → group claims → generate neutral summary |
| mT5 integration | `csebuetnlp/mT5_multilingual_XLSum` for Tamil abstractive summaries |
| Summary structure | What happened + Who involved + Agreement + Disagreements + Uncertainties |
| Summary API | Event-level Tamil summaries accessible via API |

### 📂 Files Created

```
services/nlp-engine/app/
└── summarization/
    └── mt5_summarizer.py

services/analysis-worker/app/
└── summary/
    └── event_summary.py          (evidence → structured input → mT5)
```

### ✅ Deliverable
```
→ Each event cluster gets an automatically generated neutral Tamil summary
→ Summaries reflect agreement and disagreement across sources
→ API: GET /events/{id} includes the summary
→ Summaries are versioned and updateable as new articles arrive
```

### 📝 Learning Checkpoint
> You'll understand: How abstractive summarization differs from extractive, why feeding structured evidence (not raw articles) prevents hallucination, and how multilingual models handle Tamil.

---

## Phase 7 — Frontend & Search

### 🎓 What You'll Learn
- React / Next.js fundamentals for data-driven UIs
- Building the five core screens inspired by Ground News
- Hybrid search architecture (keyword + semantic + entity + event)
- Data visualization for perspective matrices and coverage maps

### 🔨 What We'll Build

| Screen | Description (Ground News parallel) |
|---|---|
| **Home / Event Feed** | Like Ground News homepage — latest events with Orientation Bar, article count, source count |
| **Event Timeline** | Like a Ground News story page — summary + chronology + Perspective Matrix + claims + blindspots + source info |
| **Perspective Matrix** | Full-screen comparison view — source groups × framing + stance + sentiment |
| **Blindspot Feed** | Like Ground News's /blindspot — events disproportionately covered by one orientation group |
| **Source Profile** | Like Ground News's source pages — orientation + historical framing + ownership + reliability |

### 📂 Files Created

```
frontend/
├── Dockerfile
├── package.json
├── next.config.js
└── src/
    ├── components/
    │   ├── OrientationBar.jsx     (like Ground News's Bias Bar)
    │   ├── PerspectiveMatrix.jsx
    │   ├── StoryTimeline.jsx
    │   ├── BlindspotCard.jsx
    │   ├── ClaimComparison.jsx
    │   ├── SourceCard.jsx
    │   └── CoverageMatrix.jsx
    ├── pages/
    │   ├── index.jsx              (Event Feed)
    │   ├── events/[id].jsx        (Event Timeline page)
    │   ├── blindspot.jsx          (Blindspot Feed)
    │   ├── sources/[id].jsx       (Source Profile)
    │   └── search.jsx             (Search results)
    └── styles/

services/api/app/routes/
└── search.py                      (hybrid search endpoint)
```

### ✅ Deliverable
```
→ Full working frontend with 5 screens
→ Orientation Bar renders for every event
→ Perspective Matrix shows framing comparison
→ Blindspot Feed highlights coverage gaps
→ Search works across keywords, semantics, entities, and events
→ Entire platform accessible at http://localhost:3000
```

### 📝 Learning Checkpoint
> You'll understand: How to build data visualization for news intelligence, how hybrid search combines keyword and semantic retrieval, and how to present bias information responsibly in a UI.

---

## Phase 8 — Hardening & Evaluation

### 🎓 What You'll Learn
- Model evaluation — publisher-stratified splits to prevent source memorization
- Per-component metrics (Precision, Recall, F1, ARI, ROUGE)
- Caching strategies for NLP-heavy applications
- Model versioning — why every result must know which model generated it
- Creating a domain-specific Tamil annotation dataset

### 🔨 What We'll Build

| Component | Details |
|---|---|
| Evaluation framework | Per-component metrics for NER, stance, framing, event resolution, blindspots, summarization |
| Tamil annotation dataset | Manual labels for stance, framing, event pairs |
| Caching layer | Redis caching for event similarity queries, source profiles, summaries |
| Model versioning | Every NLP result tagged with model name + version |
| Logging & monitoring | Structured logging for debugging and analysis |
| Research experiments | 4 ablation studies (embedding comparison, signal combination, perspective analysis, lexical methods) |

### ✅ Deliverable
```
→ Evaluation reports for each component
→ Tamil annotation dataset (event pairs, stance labels, framing labels)
→ Sub-second API response times with caching
→ Model outputs are versioned and reproducible
→ Research experiment results documented
```

---

## Phase Summary Table

| Phase | Name | Core Deliverable | Ground News Parallel |
|---|---|---|---|
| **0** | Foundation | Docker boots, DB schema, FastAPI skeleton | — (infrastructure) |
| **1** | Ingestion | Tamil articles auto-enter database | Article ingestion from 50K+ sources |
| **2** | Event Discovery | Articles grouped into story clusters | Story clustering (merging same-event articles) |
| **3** | Framing Analysis | Perspective Matrix + Orientation Bar | Bias Bar + source comparison |
| **4** | Blindspots & Claims | Blindspot feed + claim comparison | Blindspot feed (their signature feature) |
| **5** | Source Intelligence | Orientation, ownership, reliability | Bias, Factuality, Ownership ratings |
| **6** | Summarization | Neutral Tamil event summaries | AI-generated story summaries |
| **7** | Frontend & Search | Full 5-screen UI | Web app (ground.news) |
| **8** | Hardening | Evaluation, caching, versioning | Production quality |

---

## Open Questions for Your Review

> [!IMPORTANT]
> **Before we begin Phase 0, please confirm:**
>
> 1. **API Keys** — Do you already have API keys for NewsData.io and Currents API? (Google News RSS doesn't need a key)
> 2. **GPU availability** — Do you have a GPU available for the NLP engine container? (Phase 2+ will benefit hugely from GPU; CPU is possible but much slower)
> 3. **Phase ordering** — The current order builds from bottom-up (infrastructure → data → NLP → UI). Would you prefer any different ordering?
> 4. **Frontend choice** — The plan uses React/Next.js. Do you have a preference for any other framework?
> 5. **Scope for Phase 0** — Should we include basic test scaffolding (pytest) from the start, or add testing in Phase 8?

---

*Ready to proceed? Approve this plan and we'll start with Phase 0.*
