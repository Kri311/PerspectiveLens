-- =============================================================================
-- PerspectiveLens — Phase 0 Database Schema
-- =============================================================================
--
-- Tamil News Intelligence Platform
--
-- This file is auto-executed by PostgreSQL on first container boot via
-- docker-entrypoint-initdb.d. It creates the complete schema required by
-- PerspectiveLens including:
--
--   • Required extensions (pgvector, uuid-ossp)
--   • All core tables for sources, articles, NLP analysis, events,
--     claims, coverage tracking, and summaries
--   • HNSW vector-similarity indexes for embedding search
--   • B-tree indexes for common query patterns
--   • An updated_at trigger function applied to tables that track mutations
--
-- Naming conventions:
--   Tables   — snake_case, plural nouns
--   Columns  — snake_case
--   Enums    — UPPER_CASE string literals enforced via CHECK constraints
--
-- Vector dimensions are set to 768 by default (matching common multilingual
-- transformer models). Change VECTOR(768) if you switch to a model with a
-- different output dimensionality.
--
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. Extensions
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS vector;        -- pgvector: dense-vector storage & ANN search
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4() for primary keys


-- ---------------------------------------------------------------------------
-- 2. Tables
-- ---------------------------------------------------------------------------

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- sources
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- A news outlet, website, or publishing entity from which articles are
-- collected. Each source carries an editorially-assessed political
-- orientation that feeds downstream bias and blindspot detection.
-- ---------------------------------------------------------------------------
CREATE TABLE sources (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    TEXT NOT NULL,
    domain                  TEXT,
    language                TEXT DEFAULT 'ta',
    orientation             TEXT CHECK (orientation IN (
                                'DRAVIDIAN_ORIENTED',
                                'AIADMK_ORIENTED',
                                'CONSERVATIVE_VARIABLE',
                                'POPULIST_SENSATIONAL',
                                'OTHER_UNKNOWN'
                            )),
    orientation_confidence  FLOAT,
    orientation_evidence    TEXT,
    last_reviewed           TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- source_profiles
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Aggregated statistical profiles built from a source's article history.
-- Stores frame distributions, stance distributions, and lexical signatures
-- used for comparative analysis across sources.
-- ---------------------------------------------------------------------------
CREATE TABLE source_profiles (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id                       UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    historical_frame_distribution   JSONB DEFAULT '{}',
    historical_stance_distribution  JSONB DEFAULT '{}',
    lexical_signature               JSONB DEFAULT '{}',
    article_count                   INTEGER DEFAULT 0,
    profile_period_start            TIMESTAMPTZ,
    profile_period_end              TIMESTAMPTZ,
    model_version                   TEXT
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- ownership_entities
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Corporate or individual owners behind a source. Captures parent companies,
-- political affiliations, and business interests that may influence coverage.
-- ---------------------------------------------------------------------------
CREATE TABLE ownership_entities (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id                   UUID REFERENCES sources(id) ON DELETE SET NULL,
    name                        TEXT NOT NULL,
    parent_company              TEXT,
    owner                       TEXT,
    relationships               JSONB DEFAULT '{}',
    business_interests          TEXT,
    political_or_affiliate_links TEXT,
    evidence                    TEXT,
    last_reviewed               TIMESTAMPTZ
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- articles
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Individual news articles collected from sources. The primary unit of
-- content flowing through the pipeline. status tracks where the article
-- is in the ingestion → processing → analysis lifecycle.
-- ---------------------------------------------------------------------------
CREATE TABLE articles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    canonical_url   TEXT,
    title           TEXT,
    description     TEXT,
    body            TEXT,
    image_url       TEXT,
    language        TEXT DEFAULT 'ta',
    author          TEXT,
    published_at    TIMESTAMPTZ,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    content_hash    TEXT,
    title_hash      TEXT,
    status          TEXT DEFAULT 'queued' CHECK (status IN (
                        'queued', 'processing', 'processed', 'failed'
                    )),
    raw_payload     JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(url)
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- article_chunks
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Sub-article text segments produced by the chunking stage.  Each chunk is
-- independently embedded and can be linked to fine-grained entity or claim
-- extraction results.
-- ---------------------------------------------------------------------------
CREATE TABLE article_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id      UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    text            TEXT NOT NULL,
    start_offset    INTEGER,
    end_offset      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- embeddings
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Dense vector representations of articles or article chunks, produced by
-- multilingual transformer models. Used for semantic search, event
-- clustering, and similarity comparisons.
--
-- NOTE: The VECTOR(768) dimension MUST match the embedding model's output
-- dimensionality.  If you switch models (e.g., from a 768-d model to a
-- 1024-d model), you must ALTER this column accordingly.
-- ---------------------------------------------------------------------------
CREATE TABLE embeddings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id      UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    chunk_id        UUID REFERENCES article_chunks(id) ON DELETE CASCADE,
    embedding_type  TEXT NOT NULL CHECK (embedding_type IN (
                        'TITLE', 'LEAD', 'CHUNK', 'ARTICLE'
                    )),
    model_name      TEXT NOT NULL,
    model_version   TEXT,
    vector          VECTOR(768),   -- Dimension must match embedding model output
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- entities
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Canonical named entities extracted from articles (people, organisations,
-- places, policies, etc.).  Each entity has a unique canonical_name and
-- may carry a Wikidata ID and a list of surface-form aliases.
-- ---------------------------------------------------------------------------
CREATE TABLE entities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_name  TEXT NOT NULL UNIQUE,
    entity_type     TEXT CHECK (entity_type IN (
                        'PERSON', 'ORGANIZATION', 'POLITICAL_PARTY',
                        'LOCATION', 'GOVERNMENT_BODY', 'POLICY',
                        'LAW', 'SCHEME', 'COMPANY', 'EVENT', 'DATE'
                    )),
    wikidata_id     TEXT,
    aliases         JSONB DEFAULT '[]'
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- article_entities
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Many-to-many link between articles and entities, recording every mention
-- with its surface form, extraction confidence, salience score, and
-- character position within the article body.
-- ---------------------------------------------------------------------------
CREATE TABLE article_entities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id      UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    entity_id       UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    surface_form    TEXT NOT NULL,
    confidence      FLOAT,
    salience        FLOAT,
    position        INTEGER
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- events
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- A real-world event identified by clustering related articles.  Carries a
-- representative title, an LLM-generated summary, and a centroid embedding
-- used for ongoing article assignment via similarity search.
--
-- NOTE: centroid_embedding VECTOR(768) must match the embedding model
-- dimensionality used for article embeddings.
-- ---------------------------------------------------------------------------
CREATE TABLE events (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    representative_title    TEXT,
    summary                 TEXT,
    image_url               TEXT,
    tags                    TEXT[],
    first_seen              TIMESTAMPTZ DEFAULT NOW(),
    last_updated            TIMESTAMPTZ DEFAULT NOW(),
    status                  TEXT DEFAULT 'active' CHECK (status IN (
                                'active', 'merged', 'archived'
                            )),
    cluster_confidence      FLOAT,
    centroid_embedding      VECTOR(768)   -- Dimension must match embedding model output
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- event_articles
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Junction table linking events to their constituent articles.  Records the
-- cosine similarity at assignment time and the method used (e.g.,
-- graph_clustering, manual).
-- ---------------------------------------------------------------------------
CREATE TABLE event_articles (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id                UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    article_id              UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    similarity              FLOAT,
    assignment_confidence   FLOAT,
    assignment_method       TEXT DEFAULT 'graph_clustering',
    UNIQUE(event_id, article_id)
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- article_analysis
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Per-article NLP analysis results: stance toward the event's primary
-- subject, overall sentiment, frame distribution (e.g., economic, social
-- justice, law-and-order), and a lexical signature capturing stylistic
-- markers.
-- ---------------------------------------------------------------------------
CREATE TABLE article_analysis (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id              UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    model_version           TEXT NOT NULL,
    stance                  TEXT CHECK (stance IN ('SUPPORT', 'OPPOSE', 'NEUTRAL')),
    stance_confidence       FLOAT,
    sentiment               TEXT CHECK (sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')),
    sentiment_confidence    FLOAT,
    frame_distribution      JSONB DEFAULT '{}',
    lexical_signature       JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- claims
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Discrete factual claims extracted from article text.  Each claim is
-- linked to its source article and optionally to the event it pertains to.
-- Claims are the atomic units for contradiction and entailment detection.
-- ---------------------------------------------------------------------------
CREATE TABLE claims (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id        UUID REFERENCES events(id) ON DELETE CASCADE,
    article_id      UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    claim_text      TEXT NOT NULL,
    claim_type      TEXT,
    confidence      FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- claim_relations
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Pairwise relationships between claims: entailment, neutrality, or
-- contradiction.  When a contradiction is detected, conflict_type records
-- the semantic dimension of disagreement (e.g., NUMERIC for conflicting
-- statistics, CHARACTERIZATION for differing portrayals).
-- ---------------------------------------------------------------------------
CREATE TABLE claim_relations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_a         UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    claim_b         UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    relation        TEXT NOT NULL CHECK (relation IN (
                        'ENTAILMENT', 'NEUTRAL', 'CONTRADICTION'
                    )),
    conflict_type   TEXT CHECK (conflict_type IN (
                        'NUMERIC', 'DATE', 'LOCATION', 'PERSON',
                        'EVENT_STATUS', 'CAUSALITY', 'CHARACTERIZATION'
                    )),
    confidence      FLOAT,
    UNIQUE(claim_a, claim_b)
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- event_coverage
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Tracks how each source (or source group) covers an event.  Aggregates
-- mention counts, entity-level coverage, and aspect-level coverage to
-- power blindspot and framing analysis.
-- ---------------------------------------------------------------------------
CREATE TABLE event_coverage (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id            UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    source_id           UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    source_group        TEXT,
    coverage_type       TEXT,
    mention_count       INTEGER DEFAULT 0,
    entity_coverage     JSONB DEFAULT '{}',
    aspect_coverage     JSONB DEFAULT '{}',
    last_seen           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(event_id, source_id)
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- blindspot_candidates
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Detected gaps in coverage: events, entities, or aspects that a source
-- group has ignored or under-reported relative to other groups.  Each
-- candidate goes through a lifecycle of candidate → confirmed / dismissed.
-- ---------------------------------------------------------------------------
CREATE TABLE blindspot_candidates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id        UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    source_group    TEXT NOT NULL,
    blindspot_type  TEXT NOT NULL CHECK (blindspot_type IN (
                        'EVENT', 'ENTITY', 'ASPECT'
                    )),
    score           FLOAT,
    evidence        JSONB DEFAULT '{}',
    status          TEXT DEFAULT 'candidate' CHECK (status IN (
                        'candidate', 'confirmed', 'dismissed'
                    )),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- source_reliability
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- Editorial reliability assessment for a source.  Captures historical
-- accuracy, correction track record, fact-checking outcomes, and
-- supporting evidence.
-- ---------------------------------------------------------------------------
CREATE TABLE source_reliability (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id               UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    reliability_level       TEXT CHECK (reliability_level IN (
                                'HIGH', 'MEDIUM', 'LOW'
                            )),
    historical_notes        TEXT,
    correction_history      JSONB DEFAULT '[]',
    fact_checking_history   JSONB DEFAULT '[]',
    evidence                TEXT,
    last_reviewed           TIMESTAMPTZ,
    UNIQUE(source_id)
);


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- summaries
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- LLM-generated summaries tied to events.  Multiple summaries can exist
-- per event (e.g., different summary types or model versions) to support
-- A/B evaluation and model upgrades.
-- ---------------------------------------------------------------------------
CREATE TABLE summaries (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id                UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    summary                 TEXT NOT NULL,
    summary_type            TEXT,
    model_name              TEXT,
    model_version           TEXT,
    evidence_article_count  INTEGER DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ---------------------------------------------------------------------------
-- 3. Indexes
-- ---------------------------------------------------------------------------

-- HNSW cosine-similarity indexes for approximate nearest-neighbour search
-- on embedding vectors.  These enable fast semantic search and event
-- assignment queries.
CREATE INDEX idx_embeddings_vector_hnsw
    ON embeddings
    USING hnsw (vector vector_cosine_ops);

CREATE INDEX idx_events_centroid_hnsw
    ON events
    USING hnsw (centroid_embedding vector_cosine_ops);

-- B-tree indexes for common filter and lookup patterns
CREATE INDEX idx_articles_content_hash   ON articles(content_hash);
CREATE INDEX idx_articles_url            ON articles(url);
CREATE INDEX idx_articles_source_id      ON articles(source_id);
CREATE INDEX idx_articles_published_at   ON articles(published_at);
CREATE INDEX idx_articles_status         ON articles(status);

CREATE INDEX idx_event_articles_event_id   ON event_articles(event_id);
CREATE INDEX idx_event_articles_article_id ON event_articles(article_id);

CREATE INDEX idx_article_entities_article_id ON article_entities(article_id);
CREATE INDEX idx_article_entities_entity_id  ON article_entities(entity_id);

CREATE INDEX idx_blindspot_candidates_event_id ON blindspot_candidates(event_id);


-- ---------------------------------------------------------------------------
-- 4. Trigger: auto-update updated_at on row mutation
-- ---------------------------------------------------------------------------

-- Generic trigger function that sets updated_at to the current timestamp
-- whenever a row is modified.
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to every table that carries an updated_at column.
CREATE TRIGGER trg_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_summaries_updated_at
    BEFORE UPDATE ON summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
