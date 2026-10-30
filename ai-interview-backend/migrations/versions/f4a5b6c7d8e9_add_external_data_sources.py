"""add external jobs, sync audit, and source attribution

Revision ID: f4a5b6c7d8e9
Revises: aa11bb22cc33
Create Date: 2026-08-24 15:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, None] = "aa11bb22cc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("question_bank", sa.Column("external_id", sa.String(length=160), nullable=True))
    op.add_column("question_bank", sa.Column("source_url", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_question_bank_source_external_id", "question_bank", ["source", "external_id"])

    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=True),
        sa.Column("employment_type", sa.String(length=80), nullable=True),
        sa.Column("work_type", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", JSONB(), nullable=True),
        sa.Column("apply_url", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_payload", JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_job_postings_provider_external_id"),
    )
    for name, columns in (
        ("ix_job_postings_provider", ["provider"]), ("ix_job_postings_company", ["company"]),
        ("ix_job_postings_title", ["title"]), ("ix_job_postings_published_at", ["published_at"]),
        ("ix_job_postings_last_seen_at", ["last_seen_at"]), ("ix_job_postings_is_active", ["is_active"]),
    ):
        op.create_index(name, "job_postings", columns)

    op.create_table(
        "external_sync_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="running", nullable=False),
        sa.Column("received_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_sync_runs_provider", "external_sync_runs", ["provider"])
    op.create_index("ix_external_sync_runs_resource", "external_sync_runs", ["resource"])
    op.create_index("ix_external_sync_runs_status", "external_sync_runs", ["status"])


def downgrade() -> None:
    op.drop_table("external_sync_runs")
    op.drop_table("job_postings")
    op.drop_constraint("uq_question_bank_source_external_id", "question_bank", type_="unique")
    op.drop_column("question_bank", "source_url")
    op.drop_column("question_bank", "external_id")
