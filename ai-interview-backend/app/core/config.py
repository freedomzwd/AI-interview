from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 环境配置
    ENV: str = "development"  # 默认值为 "development"

    # 基础配置
    PROJECT_NAME: str = "FastAPI Template"
    API_V1_STR: str = "/api/v1"
    API_PORT: int = 8001
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    SQL_ECHO: bool = False

    # Docker 端口配置（可选，用于 docker-compose）
    REDIS_EXTERNAL_PORT: int = 6386
    NGINX_HTTP_PORT: int = 8086
    NGINX_HTTPS_PORT: int = 8446
    FLOWER_PORT: int = 5556

    # 数据库配置
    POSTGRES_USER: str = "demo"
    POSTGRES_PASSWORD: str = "demo123"
    POSTGRES_HOST: str = "192.168.110.90"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "demo"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Celery 配置
    CELERY_BROKER_URL: str = ""  # 在 __init__ 中设置
    CELERY_RESULT_BACKEND: str = ""  # 在 __init__ 中设置

    # HTTP 代理配置 - 仅在测试环境使用
    USE_HTTP_PROXY: bool = False  # 默认不使用代理
    HTTP_PROXY: str = "http://127.0.0.1:7890"
    HTTPS_PROXY: str = "http://127.0.0.1:7890"

    # 邮件配置
    MAIL_MAILER: str = "smtp"
    MAIL_HOST: str = "localhost"
    MAIL_PORT: int = 1025
    MAIL_USERNAME: str = "user"
    MAIL_PASSWORD: str = "password"
    MAIL_FROM_ADDRESS: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "Seiki"
    MAIL_ENCRYPTION: str = "none"

    # Brevo 配置
    BREVO_API_KEY: str = "dummy-api-key"
    BREVO_EMAIL_FROM: str = "noreply@example.com"
    BREVO_EMAIL_FROM_NAME: str = "Seiki"

    # 管理员邮箱
    ADMIN_EMAIL: str = "dev@zetos.fr"

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 21600  # 15 天
    REFRESH_TOKEN_EXPIRE_DAYS: int = 15

    # S3 配置
    AWS_ACCESS_KEY_ID: str = "your-access-key"
    AWS_SECRET_ACCESS_KEY: str = "your-secret-key"
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: str = "your-bucket-name"
    AWS_ENDPOINT: str = "https://s3.amazonaws.com"

    # OpenAI 配置
    OPENAI_API_KEY: str = "your-openai-api-key"

    # DeepSeek 配置
    DEEPSEEK_API_KEY: str = "your-deepseek-api-key"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ============= RAG 知识库 / Embedding 配置 =============
    # 阿里云 DashScope（用于 Embedding 服务）
    DASHSCOPE_API_KEY: str = "sk-your-dashscope-key"

    # Embedding 模型
    KNOWLEDGE_EMBEDDING_MODEL: str = "text-embedding-v3"
    KNOWLEDGE_EMBEDDING_DIM: int = 1024

    # 文档切分参数
    KNOWLEDGE_CHUNK_SIZE: int = 500
    KNOWLEDGE_CHUNK_OVERLAP: int = 50

    # 文档检索参数（用于答案评分、用户答疑）
    KNOWLEDGE_TOP_K: int = 4
    KNOWLEDGE_MIN_SCORE: float = 0.3

    # 题库召回参数（用于面试出题，核心）
    QUESTION_BANK_MIN_SCORE: float = 0.7
    QUESTION_BANK_RECALL_FACTOR: int = 2
    QUESTION_BANK_TOP_K: int = 20
    RAG_SEARCH_MODE: str = "hybrid"
    RAG_RRF_K: int = 60

    # API 保护与可观测性
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_FAIL_OPEN: bool = False
    METRICS_ENABLED: bool = True
    METRICS_AUTH_TOKEN: str = ""
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 3

    # LangGraph Agent runtime
    AGENT_MEMORY_ENABLED: bool = True
    AGENT_POSTGRES_POOL_MAX_SIZE: int = 5
    AGENT_MAX_PARALLEL_SCOUTS: int = 3

    # Advanced RAG
    RAG_ADVANCED_ENABLED: bool = True
    RAG_MULTI_QUERY_COUNT: int = 2
    RAG_ADVANCED_CANDIDATE_K: int = 12
    RAG_RERANK_ENABLED: bool = True
    RAG_PARENT_CONTEXT_WINDOW: int = 1

    # Approved public data-source integrations. No recruitment-site scraping is used.
    EXTERNAL_SYNC_ENABLED: bool = True
    EXTERNAL_SYNC_TIMEOUT_SECONDS: int = 20
    EXTERNAL_JOB_SYNC_LIMIT: int = 100
    JOB_GREENHOUSE_BOARDS: str = ""  # Comma-separated approved Greenhouse board tokens.
    CODEFORCES_IMPORT_LIMIT: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"  # 可选，指定编码

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 在所有属性从 env 加载后设置 Celery URL
        if self.REDIS_PASSWORD:
            redis_url = (
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
            )
        else:
            redis_url = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        self.CELERY_BROKER_URL = redis_url
        self.CELERY_RESULT_BACKEND = redis_url

    @property
    def cors_origins(self) -> list[str]:
        """将逗号分隔的 CORS 配置转换为 FastAPI 所需的列表。"""
        return [item.strip() for item in self.CORS_ALLOW_ORIGINS.split(",") if item.strip()]


settings = Settings()
