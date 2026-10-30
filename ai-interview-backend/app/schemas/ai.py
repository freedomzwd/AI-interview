"""Validated contracts for model-generated data.

The LLM is an untrusted integration boundary. These models keep malformed
responses from leaking into persistence or the public API.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AIModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ResumeParseResult(AIModel):
    name: str = ""
    education: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    summary: str = ""


class ResumeAnalysisResult(AIModel):
    overall_score: float = Field(default=5.0, ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    keyword_match: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    summary: str = ""


class InterviewQuestion(AIModel):
    index: int = 0
    question: str = ""
    category: str = "technical"
    bank_id: int | None = None
    reference_answer: str | None = None
    key_points: list[str] | None = None
    source: str = "ai_fallback"


class AnswerEvaluation(AIModel):
    score: float = Field(default=5.0, ge=0, le=10)
    feedback: str = ""
    follow_up: bool = False


class QuestionScore(AIModel):
    question: str
    score: float = Field(default=0.0, ge=0, le=10)
    feedback: str = ""


class InterviewReport(AIModel):
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    hire_recommendation: str = "待定"
    question_scores: list[QuestionScore] = Field(default_factory=list)


class CandidateProfile(AIModel):
    experience_level: str = "campus"
    primary_stack: list[str] = Field(default_factory=list)
    secondary_stack: list[str] = Field(default_factory=list)
    project_directions: list[str] = Field(default_factory=list)
    strong_points: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    position_hints: list[str] = Field(default_factory=list)


class CareerAdviceResult(AIModel):
    next_actions: list[str] = Field(default_factory=list)


class RAGQueryPlan(AIModel):
    queries: list[str] = Field(default_factory=list)
    hypothetical_answer: str = ""


class RerankItem(AIModel):
    id: int
    score: float = Field(ge=0, le=10)


class RerankResult(AIModel):
    items: list[RerankItem] = Field(default_factory=list)


def model_dump_compat(model: BaseModel) -> dict[str, Any]:
    """Keep serialization in one place for Pydantic v2 model contracts."""
    return model.model_dump(exclude_none=False)
