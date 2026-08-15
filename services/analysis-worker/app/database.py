import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pgvector.sqlalchemy import Vector

DATABASE_URL_ENV = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('POSTGRES_USER', 'perslens')}:{os.getenv('POSTGRES_PASSWORD', 'lens2026')}@postgres:5432/{os.getenv('POSTGRES_DB', 'perslens')}"
)

# Force synchronous driver for Celery worker
DATABASE_URL = DATABASE_URL_ENV.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Source(Base):
    __tablename__ = 'sources'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)

class Event(Base):
    __tablename__ = 'events'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    representative_title = Column(Text)
    summary = Column(Text)
    image_url = Column(Text)
    first_seen = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    status = Column(Text, default='active')
    cluster_confidence = Column(Float)
    centroid_embedding = Column(Vector(768))

class Article(Base):
    __tablename__ = 'articles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey('sources.id'), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=True) # Adding event_id to ORM, we will run ALTER TABLE too
    url = Column(Text, nullable=False, unique=True)
    canonical_url = Column(Text)
    title = Column(Text)
    description = Column(Text)
    body = Column(Text)
    image_url = Column(Text)
    language = Column(Text, default='ta')
    author = Column(Text)
    published_at = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    content_hash = Column(Text)
    title_hash = Column(Text)
    status = Column(Text, default='queued')
    raw_payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Entity(Base):
    __tablename__ = 'entities'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name = Column(Text, nullable=False, unique=True)
    entity_type = Column(Text)
    wikidata_id = Column(Text)
    aliases = Column(JSONB, default=[])

class ArticleEntity(Base):
    __tablename__ = 'article_entities'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    entity_id = Column(UUID(as_uuid=True), ForeignKey('entities.id', ondelete='CASCADE'), nullable=False)
    surface_form = Column(Text, nullable=False)
    confidence = Column(Float)
    salience = Column(Float)
    position = Column(Integer)

class ArticleAnalysis(Base):
    __tablename__ = 'article_analysis'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    model_version = Column(Text, nullable=False, default='mDeBERTa-v3-base-mnli-xnli')
    stance = Column(Text)
    stance_confidence = Column(Float)
    sentiment = Column(Text)
    sentiment_confidence = Column(Float)
    frame_distribution = Column(JSONB, default={})
    lexical_signature = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Claim(Base):
    __tablename__ = 'claims'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'))
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(Text)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class ClaimRelation(Base):
    __tablename__ = 'claim_relations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_a = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    claim_b = Column(UUID(as_uuid=True), ForeignKey('claims.id', ondelete='CASCADE'), nullable=False)
    relation = Column(Text, nullable=False)
    conflict_type = Column(Text)
    confidence = Column(Float)

class EventCoverage(Base):
    __tablename__ = 'event_coverage'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey('sources.id', ondelete='CASCADE'), nullable=False)
    source_group = Column(Text)
    coverage_type = Column(Text)
    mention_count = Column(Float, default=0)
    entity_coverage = Column(JSONB, default={})
    aspect_coverage = Column(JSONB, default={})
    last_seen = Column(DateTime(timezone=True), default=datetime.utcnow)

class BlindspotCandidate(Base):
    __tablename__ = 'blindspot_candidates'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    source_group = Column(Text, nullable=False)
    blindspot_type = Column(Text, nullable=False)
    score = Column(Float)
    evidence = Column(JSONB, default={})
    status = Column(Text, default='candidate')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
