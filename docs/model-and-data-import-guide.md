# 模型配置与数据导入指南

本文说明项目实际使用的模型、环境变量，以及知识库和题库数据的导入方法。

## 1. 模型与供应商

| 用途 | 供应商 | 默认模型 | 必需配置 | 主要功能 |
| --- | --- | --- | --- | --- |
| 对话大模型 | DeepSeek | `deepseek-chat` | `DEEPSEEK_API_KEY` | 简历解析、岗位匹配、面试出题、回答评分、面试报告 |
| Embedding | 阿里云 DashScope | `text-embedding-v3` | `DASHSCOPE_API_KEY` | 知识文档和题库向量化、语义检索 |
| 向量存储 | PostgreSQL + pgvector | `vector(1024)` | 无外部 Key | 保存向量并执行相似度检索 |

`OPENAI_API_KEY` 当前没有接入主业务，可以保留示例值。DeepSeek 通过 OpenAI 兼容 SDK 调用，默认地址为 `https://api.deepseek.com`。

### Embedding 维度注意事项

默认配置：

```env
KNOWLEDGE_EMBEDDING_MODEL=text-embedding-v3
KNOWLEDGE_EMBEDDING_DIM=1024
```

模型输出维度必须与数据库 pgvector 字段一致。不要只修改 `KNOWLEDGE_EMBEDDING_MODEL` 或 `KNOWLEDGE_EMBEDDING_DIM` 中的一个。更换模型或维度后，需要同步修改数据库结构，并在管理端对知识库和题库执行全量重建索引。

## 2. 配置 API Key

复制环境变量模板：

```bash
cp ai-interview-backend/.env.example ai-interview-backend/.env
```

Windows PowerShell：

```powershell
Copy-Item ai-interview-backend/.env.example ai-interview-backend/.env
```

至少填写：

```env
# DeepSeek：https://platform.deepseek.com/
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# DashScope：https://dashscope.console.aliyun.com/
DASHSCOPE_API_KEY=sk-your-dashscope-key
KNOWLEDGE_EMBEDDING_MODEL=text-embedding-v3
KNOWLEDGE_EMBEDDING_DIM=1024
```

修改 `.env` 后重启服务：

```bash
docker compose up -d --build
```

`.env` 已被 Git 忽略，禁止把真实 API Key 提交到仓库。

## 3. 创建并登录管理端账号

首次启动后，在仓库根目录执行：

```bash
docker compose exec app python scripts/create_first_admin.py
```

然后访问管理端：<http://localhost:3001>

开发脚本创建的初始账号为：

```text
邮箱：admin@ai-interview.com
密码：ai-interview&admin
```

该账号仅用于本地开发。部署到公网前必须修改默认密码，并替换 `.env` 中的 `SECRET_KEY` 和数据库密码。

## 4. 导入知识库文档

知识库用于文档 RAG。导入路径：

1. 打开 <http://localhost:3001> 并登录。
2. 进入“知识库”。
3. 点击“上传文档”。
4. 选择文件，可选填标题、分类和描述。
5. 点击“上传并索引”。
6. 等待状态变为完成，然后在“检索测试”中验证召回结果。

支持格式：

- `.pdf`
- `.md`
- `.markdown`
- `.txt`

上传后系统会依次执行文本提取、分块、DashScope Embedding 向量化和 pgvector 入库。默认切分参数为：

```env
KNOWLEDGE_CHUNK_SIZE=500
KNOWLEDGE_CHUNK_OVERLAP=50
KNOWLEDGE_TOP_K=4
KNOWLEDGE_MIN_SCORE=0.3
```

可直接使用仓库示例：

```text
knowledge-base-import-samples/python-knowledge-base.md
knowledge-base-import-samples/ai-agent-engineering-knowledge.md
```

知识库向量化需要有效的 `DASHSCOPE_API_KEY`，并依赖 Redis 和 Celery Worker 正常运行。

## 5. 导入 RAG 题库

题库用于按岗位、技能和难度召回面试题，并为评分提供参考答案和采分点。导入路径：

1. 登录 <http://localhost:3001>。
2. 进入“题库管理”。
3. 点击“批量导入”。
4. 选择 `.json` 文件，或粘贴 JSON 数组。
5. 确认解析数量后提交。
6. 导入完成后等待后台向量化。
7. 在“检索测试”中输入技能关键词验证结果。

一次导入必须是非空 JSON 数组，最多 500 条。每条数据结构如下：

```json
[
  {
    "category": "technical",
    "position_tag": "python_backend",
    "difficulty": "medium",
    "question": "请解释 Python async/await 的工作原理。",
    "reference_answer": "async 定义协程函数，await 挂起当前协程并等待可等待对象完成。",
    "key_points": ["协程", "事件循环", "非阻塞", "await"],
    "tags": ["Python", "asyncio"],
    "source": "manual"
  }
]
```

字段规则：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `category` | 是 | 建议使用 `technical`、`behavioral`、`system_design` 或 `project` |
| `position_tag` | 是 | 岗位标签，例如 `python_backend`、`java_backend`、`vue_frontend`、`ai_application` |
| `difficulty` | 是 | 只能是 `easy`、`medium` 或 `hard` |
| `question` | 是 | 题目正文，不能为空 |
| `reference_answer` | 否 | 参考答案；建议填写，用于提高评分稳定性 |
| `key_points` | 否 | 字符串数组，表示采分点 |
| `tags` | 否 | 字符串数组，用于分类和检索 |
| `source` | 否 | 数据来源，默认 `manual` |

仓库提供三份可直接导入的示例：

```text
knowledge-base-import-samples/python_backend_questions_20.json
knowledge-base-import-samples/python_ai_application_questions_20.json
knowledge-base-import-samples/agent_development_questions_15.json
```

其中 `agent_development_questions_15.json` 覆盖 Tool Calling、状态与工作流、记忆、RAG、多 Agent、结构化输出、安全与可观测性；`python_ai_application_questions_20.json` 覆盖 AI 应用工程和 RAG。当前版本实机截图使用后两份数据，共 35 道题，全部完成向量化。

题目会先写入数据库，再由 Celery 异步生成 Embedding。向量化同样需要有效的 `DASHSCOPE_API_KEY`。

## 6. 推荐的首次运行顺序

```text
1. docker compose up -d --build
2. 配置 DeepSeek 和 DashScope API Key
3. 创建初始管理员
4. 导入知识库文档
5. 导入题库 JSON
6. 在管理端执行知识库和题库检索测试
7. 打开用户端上传简历并发起模拟面试
```

服务地址：

| 服务 | 地址 |
| --- | --- |
| 用户端 | <http://localhost:3000> |
| 管理端 | <http://localhost:3001> |
| 后端健康检查 | <http://localhost:8006/api/v1/config/health> |
| 用户 API 文档 | <http://localhost:8006/client/docs> |
| 管理 API 文档 | <http://localhost:8006/backoffice/docs> |

## 7. 常见问题

### 文档或题库一直没有向量化

检查 `DASHSCOPE_API_KEY`，并确认 Celery Worker 与 Redis 正常：

```bash
docker compose ps
docker compose logs --tail 100 celery-worker
```

### AI 出题或评分失败

检查 `DEEPSEEK_API_KEY`、账户余额和网络连接：

```bash
docker compose logs --tail 100 app
```

### 更换 Embedding 模型后检索异常

确认模型维度与 `KNOWLEDGE_EMBEDDING_DIM`、数据库向量字段一致，并在管理端重新构建全部知识库和题库向量。
