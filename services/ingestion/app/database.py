import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('POSTGRES_USER', 'perslens')}:{os.getenv('POSTGRES_PASSWORD', 'lens2026')}@postgres:5432/{os.getenv('POSTGRES_DB', 'perslens')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    domain = Column(Text)
    language = Column(Text, default='ta')
    orientation = Column(Text)
    orientation_confidence = Column(Float)
    orientation_evidence = Column(Text)
    last_reviewed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    canonical_url = Column(Text)
    title = Column(Text)
    description = Column(Text)
    body = Column(Text)
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
