"""Prometheus metrics shared by the API, LLM and RAG layers."""

from prometheus_client import Counter, Histogram


API_REQUESTS = Counter(
    "ai_interview_api_requests_total",
    "Total HTTP requests handled by the API",
    ("method", "path", "status"),
)
API_LATENCY = Histogram(
    "ai_interview_api_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "path"),
)

LLM_REQUESTS = Counter(
    "ai_interview_llm_requests_total",
    "Total LLM requests",
    ("operation", "status"),
)
LLM_LATENCY = Histogram(
    "ai_interview_llm_duration_seconds",
    "LLM request duration in seconds",
    ("operation",),
)

RAG_REQUESTS = Counter(
    "ai_interview_rag_requests_total",
    "Total RAG retrieval requests",
    ("retriever", "mode"),
)
RAG_LATENCY = Histogram(
    "ai_interview_rag_duration_seconds",
    "RAG retrieval duration in seconds",
    ("retriever", "mode"),
)

CELERY_TASKS = Counter(
    "ai_interview_celery_tasks_total",
    "Total Celery task outcomes",
    ("task", "status"),
)

AGENT_RUNS = Counter(
    "ai_interview_agent_runs_total",
    "Total LangGraph agent runs",
    ("status",),
)
AGENT_NODE_LATENCY = Histogram(
    "ai_interview_agent_node_duration_seconds",
    "LangGraph node duration in seconds",
    ("node",),
)
AGENT_MEMORY_OPERATIONS = Counter(
    "ai_interview_agent_memory_operations_total",
    "Long-term memory operations",
    ("operation", "status"),
)
RAG_ADVANCED_OPERATIONS = Counter(
    "ai_interview_rag_advanced_operations_total",
    "Advanced RAG operations",
    ("operation", "status"),
)
