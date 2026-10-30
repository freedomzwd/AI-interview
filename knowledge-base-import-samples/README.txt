Import-ready data for the two RAG systems in the admin console.

Question bank JSON:
- python_backend_questions_20.json
- python_ai_application_questions_20.json
- agent_development_questions_15.json

Knowledge base Markdown:
- python-knowledge-base.md
- ai-agent-engineering-knowledge.md

Import these files from the admin console. Question and document embeddings are
generated asynchronously by Celery and require a valid DashScope API key.
