"""add PostgreSQL full-text indexes for hybrid RAG

Revision ID: aa11bb22cc33
Revises: f3a4b5c6d7e8
Create Date: 2026-08-24 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "aa11bb22cc33"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_question_bank_fts
        ON question_bank
        USING gin (
            to_tsvector(
                'simple',
                coalesce(question, '') || ' ' || coalesce(reference_answer, '')
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_fts
        ON knowledge_chunks
        USING gin (to_tsvector('simple', coalesce(content, '')))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_question_bank_fts")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_fts")
