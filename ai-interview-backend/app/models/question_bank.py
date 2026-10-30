from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from .base import BaseModel


class QuestionBank(BaseModel):
    __tablename__ = "question_bank"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_question_bank_source_external_id"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)        # technical / behavioral / system_design / project
    position_tag = Column(String(100), nullable=False, index=True)   # python_backend / java_backend / vue_frontend
    difficulty = Column(String(20), nullable=False, index=True)      # easy / medium / hard
    question = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=True)
    key_points = Column(JSONB, nullable=True)   # ["要点1", "要点2"]
    tags = Column(JSONB, nullable=True)         # ["GIL", "并发"]
    embedding = Column(Vector(1024), nullable=True)     # 题面+答案拼接后的向量
    embedding_text = Column(Text, nullable=True)        # 用于生成 embedding 的原始文本（便于调试/重建）
    source = Column(String(50), default="manual")       # manual / imported / ai_generated
    external_id = Column(String(160), nullable=True)     # upstream provider-specific stable identifier
    source_url = Column(Text, nullable=True)             # original problem URL for attribution
    use_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("admins.id"), nullable=True)
