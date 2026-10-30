"""Normalized job postings from approved public employer/job-board APIs."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class JobPosting(BaseModel):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_job_postings_provider_external_id"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    external_id = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False, index=True)
    title = Column(String(300), nullable=False, index=True)
    location = Column(String(300), nullable=True)
    employment_type = Column(String(80), nullable=True)
    work_type = Column(String(80), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)
    apply_url = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, index=True)
    raw_payload = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
