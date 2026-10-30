"""Audit log for external data synchronization jobs."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from .base import BaseModel


class ExternalSyncRun(BaseModel):
    __tablename__ = "external_sync_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    resource = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="running", index=True)
    received_count = Column(Integer, nullable=False, default=0)
    created_count = Column(Integer, nullable=False, default=0)
    updated_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
