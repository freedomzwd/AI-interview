# AI Interview Agent 系统化学习路线图

> 本路线图基于本仓库当前代码（`master` 分支）生成，所有文件路径、配置参数、端口均与源码核对一致。
> 目标：从"看懂业务代码"到"理解架构设计"，最终具备**独立维护、排查问题、二次开发**的能力。

---

## 目录

- [一、全局认知：先建立系统地图](#一全局认知先建立系统地图)
- [二、阶段一：基础认知与环境搭建](#二阶段一基础认知与环境搭建)
- [三、阶段二：核心业务链路（前后端交互）](#三阶段二核心业务链路前后端交互)
- [四、阶段三：AI 核心能力（Agent 与 RAG）](#四阶段三ai-核心能力agent-与-rag)
- [五、阶段四：工程化与异步处理](#五阶段四工程化与异步处理)
- [六、阶段五：容器化部署与进阶优化](#六阶段五容器化部署与进阶优化)
- [七、附录](#七附录)

---

## 一、全局认知：先建立系统地图

### 1.1 系统一图流

```text
┌─────────────────┐   ┌─────────────────┐
│ 用户端 Vue3      │   │ 管理端 Vue3      │
│ :3000           │   │ :3001           │
│ 简历/匹配/面试/报告│   │ 题库/知识库/岗位模板│
└────────┬────────┘   └────────┬────────┘
         │  Vite 代理 /api      │
         ▼                     ▼
┌──────────────────────────────────────────────┐
│ FastAPI 后端 (app :8006)                       │
│  api 层(client/backoffice) → services 层       │
│  ├─ 岗位匹配 Agent (LangGraph + Postgres 持久化) │
│  ├─ 题库 RAG / 知识库 RAG (pgvector)            │
│  ├─ AI 能力中枢 ai_service.py (DeepSeek)        │
│  └─ JWT 双域鉴权 (scope: client / backoffice)   │
├──────────────────────────────────────────────┤
│ PostgreSQL+pgvector :5434   Redis :6382       │
│ (结构化数据+向量)             (Broker/缓存/验证码/限流)│
│ Celery worker + beat (文档入库/批量向量化/外部同步)   │
│ Nginx :8080/:8443   Flower :5555(可选)         │
└──────────────────────────────────────────────┘
```

### 1.2 核心业务主线（务必先背下来）

```
上传简历 → AI 解析落库 → 岗位匹配 Agent 推荐岗位
→ 发起面试（题库 RAG 召回 + AI 选题微调，不足则二次召回/兜底补题）
→ 逐题作答（流式评分，注入 reference_answer + key_points）
→ 生成结构化面试报告
```

### 1.3 三个子项目

| 目录 | 角色 | 技术栈 |
| --- | --- | --- |
| `ai-interview-backend/` | FastAPI 后端 + Celery + 迁移 | Python 3.12 / FastAPI 0.115 / SQLAlchemy 2.x / LangGraph 0.3 |
| `ai-interview-frontend/` | 候选人端 | Vue 3.4 + Vite 5 + Pinia + Axios（纯 JS，无 UI 库，自研 CSS） |
| `ai-interview-admin/` | 管理端 | 同上，端口 3001，API 前缀 `/api/v1/backoffice` |

### 1.4 使用方法

- **建议总周期**：4~6 周（阶段一 3~4 天 / 阶段二 1 周 / 阶段三 1.5~2 周 / 阶段四 1 周 / 阶段五 1 周起），可按基础调整。
- **每阶段学习循环**：`概览文档 → 精读源码 → 动手跑通 → 改参数观察 → 输出笔记/图`。只读不跑，收获减半。
- **配套文档**：本仓库自带 `README.md`、`docs/model-and-data-import-guide.md`、`rag-implementation.md`、`deployment-guide.md`、`project-q-and-a.md`、`interview-notes.md`，路线图中会标注在何时读哪份。
- **前置知识要求**：Python 基础、HTTP/REST 概念、SQL 基础、JavaScript 基础。缺 Vue 或 FastAPI 经验不影响，路线内安排了对应补课点。

---

## 二、阶段一：基础认知与环境搭建

> **建议周期**：3~4 天
> **阶段主题**：知道这个项目"是什么、有什么、怎么跑起来"。

### 2.1 学习目标

1. 理解项目定位：不是单一 Prompt Demo，而是覆盖"简历解析 → 岗位匹配 → RAG 出题 → AI 评分 → 报告"的完整 AI 应用工程。
2. 能用 Docker Compose 一键启动全部服务，并理解每个容器的职责。
3. 熟悉后端分层结构（api / schemas / services / models）与配置体系。
4. 完成首次数据准备：管理员账号、题库样例、知识库样例、API Key。

### 2.2 核心技术栈（本阶段）

| 技术 | 在本项目中的应用 | 学到什么程度 |
| --- | --- | --- |
| Docker / Docker Compose | 一键编排 8 个服务，`include` 组合多个 compose 文件 | 会 `up/down/ps/logs/exec`，能看懂 service 定义 |
| FastAPI | 后端框架：依赖注入、Pydantic 校验、异步路由 | 知道路由/依赖注入基本概念即可 |
| pydantic-settings | `app/core/config.py` 统一配置，`.env` 注入 | 理解"配置即代码"的分层思路 |
| PostgreSQL + pgvector | 结构化数据 + 1024 维向量同库存放 | 会连库、会 `SELECT`，知道 pgvector 是扩展 |
| Redis | Celery Broker、验证码、限流 | 知道它是内存 KV + 消息中间件 |

### 2.3 阅读清单（按顺序）

| # | 材料 | 关注点 |
| --- | --- | --- |
| 1 | `README.md` | 通读。重点：核心亮点、系统架构图、业务流程四步 |
| 2 | `docs/model-and-data-import-guide.md` | 模型配置（DeepSeek 对话 / DashScope Embedding）、管理员创建、数据导入的**首次运行顺序** |
| 3 | 根目录 `docker-compose.yml` | 只有两个服务（frontend、admin），注意 `include` 引入了后端的两个 compose 文件——这是"组合式编排"设计 |
| 4 | `ai-interview-backend/docker-compose.yml` | 7 个服务逐个看：`app`、`celery-worker`、`celery-beat`、`postgres`(pgvector/pgvector:pg16)、`redis`、`nginx`、`flower`(profiles: monitoring)。注意每个 `healthcheck` 与 `depends_on: condition: service_healthy` |
| 5 | `ai-interview-backend/app/core/config.py` | 全部配置项一览。注意两处设计：① `__init__` 里动态拼 `CELERY_BROKER_URL`；② compose 里用环境变量覆盖默认值（如 `POSTGRES_HOST=postgres`），理解"默认值只用于裸跑，容器内靠环境变量覆盖" |
| 6 | `ai-interview-backend/app/route/route.py` | 应用工厂 `create_app()`：lifespan 启停（agent_runtime、日志消费线程）、CORS、异常处理器、`/uploads/avatars` 静态挂载 |
| 7 | `ai-interview-backend/app/route/router_registry.py` | 所有路由的注册中心——本项目的"接口总目录"，后续阶段反复回来查 |

### 2.4 动手实践

1. **一键启动**：`docker compose up -d --build`，用 `docker compose ps` 确认全部容器 healthy。
2. **健康检查三连**：
   - 浏览器访问 `http://localhost:8006/api/v1/config/health`（检查 API/PG/Redis 状态）；
   - 访问 `http://localhost:3000`（用户端）与 `http://localhost:3001`（管理端）；
   - 打开浏览器 DevTools 观察前端请求如何走 Vite 代理 `/api → VITE_PROXY_TARGET`（见两个前端的 `vite.config.js`）。
3. **配置 API Key**：复制 `ai-interview-backend/.env.example` 为 `.env`，填入 **DeepSeek Key**（对话：简历解析/出题/评分/报告）与 **DashScope Key**（Embedding），重启 `app` 与 `celery-worker`。
4. **初始化数据**：
   - `docker compose exec app python scripts/create_first_admin.py` 创建超级管理员；
   - `docker compose exec app python scripts/seed_position_templates.py` 灌入岗位模板（Agent 的匹配数据源）；
   - 登录管理端，用 `knowledge-base-import-samples/` 下的 JSON 批量导入题库，上传一份 Markdown 知识库文档。
5. **进容器看数据库**：`docker compose exec postgres psql -U demo -d ai_interview`，执行 `\dt` 看所有表，`SELECT * FROM question_bank LIMIT 3;` 看 `embedding` 列。

### 2.5 产出与检验标准

- [ ] 全部容器可一键启动，能解释每个容器是干什么的。
- [ ] 能画出（手画即可）1.1 的系统图，标注端口与依赖方向。
- [ ] 能说出：用户端 3000 / 管理端 3001 / 后端 8006 / PG 5434 / Redis 6382 / Nginx 8080 / Flower 5555 分别是谁。
- [ ] 管理端能看到导入的题库与知识库文档，`question_bank` 表中 `embedding` 列非空。
- [ ] 能回答：**为什么核心服务不配 `.env` 也能启动，而 AI 功能必须配 Key？**（提示：compose 提供了安全默认值，外部模型服务无法兜底）

### 2.6 自测题

1. `docker-compose.yml` 里的 `include` 和 `extends` 有什么区别？本项目为什么要拆成多个 compose 文件？
2. `app` 服务的 healthcheck 是怎么实现的？为什么前端要 `depends_on: condition: service_healthy` 而不是简单依赖启动顺序？
3. `config.py` 中 `RAG_SEARCH_MODE`、`QUESTION_BANK_MIN_SCORE` 这些配置在 compose 里被再次声明，这说明了什么配置管理策略？

---

## 三、阶段二：核心业务链路（前后端交互）

> **建议周期**：1 周
> **阶段主题**：跟着"一次完整面试"走通前后端，掌握鉴权、简历、面试三大链路与 SSE 流式交互。

### 3.1 学习目标

1. 掌握 JWT 双域鉴权机制（client / backoffice 两套 scope）。
2. 走通"注册登录 → 上传简历 → AI 解析 → 发起面试 → 流式作答 → 报告"全链路，能说出每一步落在哪个文件。
3. 理解前端 axios 拦截器 + Pinia 状态管理 + 路由守卫的协作方式。
4. 掌握本项目 SSE 的实现方式（后端 `StreamingResponse` + 前端 `fetch` + `ReadableStream`，**不是** EventSource）。

### 3.2 核心技术栈（本阶段）

| 技术 | 应用场景 | 设计考量 |
| --- | --- | --- |
| JWT (python-jose, HS256) | access token 30min + refresh token 7 天，含 `scope` 与 `jti` | 用 scope 区分用户端/管理端，同一套 `AuthBase` 复用 |
| passlib + bcrypt | 密码哈希 | 不可逆存储 |
| Pydantic Schemas | `app/schemas/` 按 client/backoffice 拆分 | 请求/响应契约与 ORM 模型解耦 |
| pdfplumber | 简历 PDF 文本提取 | 纯文本解析后交给 LLM 结构化 |
| SSE (Server-Sent Events) | 面试作答流式评分反馈 | 单向推送即可满足需求，比 WebSocket 轻；前端用 `fetch` 流读取是因为要 **POST** 请求体，`EventSource` 只支持 GET |
| Pinia + vue-router 守卫 | 登录态持久化（localStorage）+ 路由拦截 | 前端无 UI 库，逻辑集中在 stores 与 views |

### 3.3 源码精读路线（按链路顺序）

#### 链路 A：鉴权

1. `app/core/security.py` — `AuthBase`：`create_access_token`（含 scope + jti）、`create_refresh_token`、`verify_token`、bcrypt 哈希。
2. `app/api/client/deps.py` 与 `app/api/backoffice/deps.py` — `get_current_user` 依赖：Bearer 解析 → 校验 scope → 查库。体会"依赖注入做鉴权"的 FastAPI 惯用法。
3. `app/api/client/v1/auth.py` + `app/services/client/auth.py` — 注册/登录/刷新/邮箱验证；配套 `redis_verification.py`（验证码存 Redis，顺带预习阶段四的 Redis 用法）。
4. 前端：`ai-interview-frontend/src/api/request.js` — **必读**。看请求拦截器注入 token、响应拦截器解包 `{code, data}`、401/403 自动登出、422 校验错误解析。
5. `src/stores/auth.js` 与 `src/router/index.js` — Pinia 登录态 + `beforeEach` 路由守卫。

#### 链路 B：简历上传与解析

1. `app/api/client/v1/resume.py` — `POST /resumes`（multipart 文件上传）。
2. `app/services/client/resume_service.py` — 上传编排。
3. `app/services/client/ai_service.py` — **本阶段最重要的文件**，项目的"AI 能力中枢"：重点读 `parse_resume`（DeepSeek 结构化）与 **JSON 提取 + 修复**逻辑（LLM 输出不稳定时的工程兜底），理解 `LLM_TIMEOUT_SECONDS=60` / `LLM_MAX_RETRIES=3` 如何生效。
4. 数据落点：`resumes` 表的 `parsed_content`(JSON) 与 `analysis` 字段。

#### 链路 C：面试主流程

1. `app/api/client/v1/interview.py` — 四个关键端点：`POST /start`、`POST /{id}/answer`、`POST /{id}/answer/stream`（SSE）、`GET /{id}/report`。
2. `app/services/client/interview_service.py` — **通读**。三条主线：
   - `start`：结合岗位 + 简历技能构造 query → RAG 召回 → AI 选题（本阶段只需知道"这里调了 RAG"，细节留到阶段三）；
   - `answer`：取当前题 `reference_answer` + `key_points` 注入评分 Prompt → 流式返回；
   - `report`：整场报告生成。
3. `app/services/client/ai_service.py` 的 `evaluate_answer` / `stream` / `generate_report`。
4. 数据落点：`interviews.questions_data`(JSONB)、`interview_messages`（每轮 role/content/score/feedback）。

#### 链路 D：前端面试房间

1. `ai-interview-frontend/src/api/interview.js` — **必读 `submitAnswerStream()`**：`fetch` POST → `response.body.getReader()` 逐块读取 → 按 `data: ` 行解析 SSE → 分发 `chunk`（增量文本）与 `done`（score/next_question/is_finished）事件。
2. `src/views/Interview.vue` — 面试房间：流式渲染 + JSON 评分块过滤（正则剥离）+ 打字机效果。
3. `src/views/Report.vue`、`src/views/Dashboard.vue` — 报告展示与历史记录。

### 3.4 动手实践

1. **不用浏览器走一遍接口**：用 curl/httpie 或 Swagger（开发模式下后端挂载了 `/client`、`/backoffice` 两份 Swagger）依次调用：注册 → 登录拿 token → 上传一份 PDF 简历 → 发起面试 → 提交一次回答。把每个响应体记在笔记里。
2. **DevTools 观察 SSE**：浏览器进入面试房间作答，打开 Network 面板找到 `answer/stream` 请求，观察响应体逐行出现 `data: ...`；再看前端如何渲染。
3. **断点式读库**：面试发起后立刻查库：`SELECT questions_data FROM interviews ORDER BY id DESC LIMIT 1;` 看出题结构（题目 + 参考答案 + 采分点是如何带进会话的）。
4. **改一个小功能**：在 `Interview.vue` 的流式渲染里加一个"AI 正在输入"的状态提示，或在报告页加一句总结文案——体会最小闭环的前端改动。
5. **管理端走查**：登录管理端，过一遍 `Interviews` / `InterviewDetail`（面试记录只读回放），理解管理端数据从哪些 backoffice 接口来（`app/api/backoffice/v1/interviews.py`）。

### 3.5 产出与检验标准

- [ ] 手绘三张时序图：① 登录与 token 刷新；② 简历上传→解析→落库；③ 发起面试→流式作答→评分入库。
- [ ] 能脱口说出：`request.js` 的两个拦截器分别做了什么；管理端 baseURL 为什么是 `/api/v1/backoffice`。
- [ ] 能解释：为什么 SSE 用 `fetch` 而不是 `EventSource`？为什么评分必须注入 `reference_answer` 和 `key_points`？
- [ ] 完成一次"最小前端改动"并本地验证。
- [ ] 自测：一个 401 响应从后端发出后，前端会经过哪些代码、最终用户看到什么？

---

## 四、阶段三：AI 核心能力（Agent 与 RAG）

> **建议周期**：1.5~2 周（本路线的核心）
> **阶段主题**：吃透岗位匹配 Agent（LangGraph）与双路 RAG（题库 + 知识库）的设计与实现。
> **配套必读**：根目录 `rag-implementation.md`（26KB，RAG 链路官方说明），建议在本阶段中期读，先自己读代码再对照。

### 3A. 岗位匹配 Agent（LangGraph）

#### 学习目标

1. 理解 LangGraph 的 `StateGraph` / 节点 / 条件边 / `Send` 并行扇出模型。
2. 掌握本项目 Agent 的持久化设计：Postgres Checkpointer（会话状态）+ Postgres Store（长期记忆）。
3. 能独立调试单个 Agent 工具，并解释整条图的执行轨迹。

#### 源码精读路线

| # | 文件 | 关注点 |
| --- | --- | --- |
| 1 | `app/agents/state.py` | `PositionAgentState` TypedDict。重点看 `Annotated[list, operator.add]` 这类**归并器**（`scout_results`、`completed_steps`、`errors` 是累加字段）——并行节点写同一字段不打架的关键 |
| 2 | `app/agents/position_graph.py` | **核心**。`build_position_graph()` 七个节点：`load_context` → `resume_analyst` →（条件边 `Send` 扇出 N 个）`position_scout` → `merge_positions` → `interview_planner` → `career_advisor` → `memory_writer`。理解 map-reduce 结构 |
| 3 | `app/agents/runtime.py` | `AgentRuntime`：`AsyncConnectionPool` → `AsyncPostgresSaver`(checkpointer) + `AsyncPostgresStore`(长期记忆)；单例 `agent_runtime` 在 lifespan 中启停 |
| 4 | `app/agents/memory.py` | `AgentMemoryService`：namespace `("users", user_id, "career")` 下的候选人画像读写——Agent 跨会话记忆的落点 |
| 5 | `app/agents/setup_storage.py` | 幂等初始化 checkpoint/store 表，理解"启动即就绪"的设计 |
| 6 | `app/services/client/position_agent_tools.py` | **五个工具逐个精读**：`get_parsed_resume`、`build_candidate_profile`（LLM 抽画像）、`match_positions`（对 `position_templates` 做加权技能匹配打分）、`get_position_interview_focus`、`start_mock_interview`（复用 RAG 出题管道，把 Agent 和面试主流程接起来） |
| 7 | `app/services/client/position_agent_service.py` | facade：run/resume 图执行，对外屏蔽 LangGraph 细节 |
| 8 | `app/api/client/v1/position_agent.py` | `POST /position-agent/match`、`POST /start-interview`；前端对应 `src/views/PositionMatch.vue`（注意该请求超时 3 分钟，为什么？） |

#### 设计考量（边读边思考）

- 为什么用**显式图编排**（固定节点流）而不是 ReAct 自由工具调用？——可解释、可调试、可展示执行过程（前端有流程高亮），业务路径本来就是确定的。
- `AGENT_MAX_PARALLEL_SCOUTS=3` 限制并行扇出，防止一次性对 N 个岗位方向并发匹配打爆资源。
- checkpoint 存 Postgres 而非内存：服务重启不丢运行中的 Agent 状态，且支持"断点续跑"。

#### 动手实践

1. 用户端走一次 `/position-match` 完整流程，同时在 `docker compose logs -f app` 里看节点执行日志，把七个节点的执行顺序记下来。
2. **单工具调试**：写个临时脚本（或用 `python -i`）直接调 `match_positions`，传入一段简历画像，观察打分结果；再改 `position_templates` 表里某个岗位的 `core_skills`，看分数变化。
3. 查 checkpoint 表：进 psql 看 LangGraph 自动建的表（`checkpoints`、`store` 相关），理解状态是怎么持久化的。
4. **进阶**：临时关闭 `AGENT_MEMORY_ENABLED=false`，对比两次运行的 `career_advisor` 输出，体会长期记忆的作用。

### 3B. RAG 双管道（题库 + 知识库）

#### 学习目标

1. 掌握"切分 → 向量化 → 存储 → 召回 → 融合 → 重排"完整管道，并知道本项目两套 RAG 的差异。
2. 掌握四种检索模式（semantic / keyword / hybrid / advanced）的切换与原理。
3. 能调整召回参数并用评估脚本量化效果。

#### 源码精读路线

| # | 文件 | 关注点 |
| --- | --- | --- |
| 1 | `app/services/common/embedding.py` | DashScope `text-embedding-v3`（1024 维）单例封装，批量 25 条，异步/同步双接口。**设计考量**：为什么题库和知识库共用同一个 embedding 服务（维度一致才能同库同索引） |
| 2 | `app/services/backoffice/knowledge_service.py` | 知识库入库：文本抽取 → `RecursiveCharacterTextSplitter`（`chunk_size=500`、`overlap=50`、中文友好分隔符）→ 向量化 → `knowledge_chunks`。切分参数来自 `KNOWLEDGE_CHUNK_SIZE/KNOWLEDGE_CHUNK_OVERLAP` |
| 3 | `app/services/backoffice/question_bank_service.py` | 题库入库：**题目 + 参考答案拼接后向量化**（为什么？——让 query 无论像"问题"还是像"答案"都能命中）；混合检索；`use_count` 统计 |
| 4 | `app/services/common/rag.py` | `reciprocal_rank_fusion()`（RRF，k 默认 60）与分数归一化——hybrid 模式的融合核心，手推一遍 RRF 公式 |
| 5 | `app/services/common/advanced_rag.py` | 高级 RAG 三件套：**多查询扩展**（LLM 生成 2 个改写 query + 1 个假想答案）、**LLM-as-reranker**（`RAG_RERANK_ENABLED`）、**父窗口上下文扩展**（`RAG_PARENT_CONTEXT_WINDOW=1`，命中 chunk 后带上相邻 chunk） |
| 6 | `app/services/client/interview_service.py` 的 `_generate_questions_with_rag` | **RAG 与业务的结合点**：`QUESTION_BANK_TOP_K=20` 召回 → `QUESTION_BANK_MIN_SCORE=0.7` 过滤 → `QUESTION_BANK_RECALL_FACTOR=2` 超量召回给选题留余地 → 不足时二次召回 + AI 兜底补题。这是"召回为业务服务"的范本 |
| 7 | `app/models/` 中 `KnowledgeChunk` / `QuestionBank` | `embedding Vector(1024)` 列；去 psql 里找到向量索引定义（IVFFlat/HNSW）与全文索引（配合 `websearch_to_tsquery` 的关键词路） |

#### 关键参数速查（`app/core/config.py`）

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `RAG_SEARCH_MODE` | `hybrid` | semantic / keyword / hybrid / advanced |
| `RAG_RRF_K` | 60 | RRF 融合平滑常数 |
| `QUESTION_BANK_TOP_K` | 20 | 题库召回条数 |
| `QUESTION_BANK_MIN_SCORE` | 0.7 | 题库相关性门槛 |
| `QUESTION_BANK_RECALL_FACTOR` | 2 | 超量召回倍数 |
| `KNOWLEDGE_CHUNK_SIZE / OVERLAP` | 500 / 50 | 知识库切分 |
| `KNOWLEDGE_TOP_K / MIN_SCORE` | 4 / 0.3 | 知识库检索 |
| `RAG_ADVANCED_ENABLED` | true | 高级 RAG 总开关 |
| `RAG_MULTI_QUERY_COUNT` | 2 | 查询改写数量 |
| `RAG_ADVANCED_CANDIDATE_K` | 12 | 重排候选数 |
| `RAG_RERANK_ENABLED` | true | LLM 重排开关 |
| `RAG_PARENT_CONTEXT_WINDOW` | 1 | 父窗口扩展半径 |

#### 动手实践

1. **管理端检索测试页**：`/question-bank/test` 与 `/knowledge/test`，用同一个 query（如"Redis 分布式锁怎么实现"）分别测试，记录命中与分数。
2. **模式对比实验**：改环境变量 `RAG_SEARCH_MODE` 为 `semantic` → `keyword` → `hybrid` → `advanced`（重启 app），对同一组 query 对比召回差异，整理成表格。重点观察：纯关键词模式下语义相近但措辞不同的 query 会不会漏召回。
3. **参数调优实验**：把 `KNOWLEDGE_CHUNK_SIZE` 从 500 调到 1000、`OVERLAP` 调到 200，重新上传同一份文档（走管理端 reindex 或删除重传），对比检索质量；再用管理端"查看分块"页直观感受切分差异。
4. **跑评估脚本**：`docker compose exec app python scripts/evaluate_rag.py`（数据集参考 `scripts/rag_eval.example.json`），并**自己造 5 条评估 query**，体会"检索质量如何被量化"。
5. **SQL 级验证**：进 psql 手写一条向量查询：
   ```sql
   SELECT question, 1 - (embedding <=> query_vector) AS score
   FROM question_bank ORDER BY embedding <=> query_vector LIMIT 5;
   ```
   （query_vector 可用临时 Python 脚本调 embedding 服务生成），验证应用层召回与裸 SQL 一致。
6. **追踪一次完整出题**：从发起面试开始打日志/断点，记录"构造 query → embedding → 召回 → 过滤 → AI 选题 → 兜底"每一步的实际数据。

### 3.6 阶段产出与检验标准

- [ ] 手绘 LangGraph 岗位匹配图（节点 + 边 + 扇出），标出每个节点读写了 State 的哪些字段。
- [ ] 手绘 RAG 管道图，标出两套 RAG 的差异点（入库文本构成、检索用途、阈值参数）。
- [ ] 完成四模式检索对比表 + 一次参数调优实验记录。
- [ ] 能解释：RRF 为什么用排名而不是分数融合？题库为什么把"题目+参考答案"一起向量化？`MIN_SCORE=0.7` 设得过高/过低各会发生什么？
- [ ] 能独立完成：新增一个 Agent 工具（如"查询岗位平均薪资"）并挂到图里跑通——这是阶段五二次开发的热身。

---

## 五、阶段四：工程化与异步处理

> **建议周期**：1 周
> **阶段主题**：理解让系统"可靠运转"的部分——Celery 异步、Redis 多用途、迁移、测试、可观测与安全。

### 4.1 学习目标

1. 掌握 Celery 在本项目的完整形态：broker/backend 配置、任务定义、beat 定时、worker 部署与监控。
2. 理解"什么操作必须异步"：文档入库（抽取+切分+批量 embedding 可达分钟级）、批量向量化、外部数据同步、邮件。
3. 掌握 Alembic 迁移流程，能为新字段生成并应用迁移。
4. 了解项目的可观测性（Prometheus、日志、Flower）与安全中间件（限流、CSP/HSTS）。

### 4.2 核心技术栈（本阶段）

| 技术 | 应用场景 | 设计考量 |
| --- | --- | --- |
| Celery 5.5 | worker + beat 双进程；任务见下表 | HTTP 请求不等待重活，上传即返回，任务后台消化 |
| Redis 7 | 一身四职：Celery broker/result backend、邮箱验证码（`redis_verification.py`）、`fastapi-limiter` 限流后端、通用缓存 | 单组件多用途，降低运维面 |
| Alembic | `migrations/` 9 个版本，覆盖建表、知识库、岗位模板、全文索引等 | schema 变更可追溯、可重放 |
| pytest | `tests/`：`test_smoke.py` / `test_security.py` / `test_agent_rag.py` | 冒烟 + 安全 + AI 集成三层 |
| prometheus-client | metrics 中间件（`METRICS_ENABLED`，`METRICS_AUTH_TOKEN` 保护） | 生产可观测 |
| fastapi-limiter | API 限流（`RATE_LIMIT_ENABLED`、`RATE_LIMIT_FAIL_OPEN`） | 防滥用，失败策略可配 |

### 4.3 源码精读路线

1. `app/core/celery_app.py` — Celery 实例：broker/backend 均指向 Redis（回看 `config.py` 的 `__init__` 拼接逻辑）；`include` 注册了哪些任务模块。
2. `app/schedule/jobs/` 任务全览：

   | 任务文件 | 任务 | 触发方式 |
   | --- | --- | --- |
   | `knowledge_tasks.py` | `ingest_document_task`（下载→抽取→切分→向量化→入库）、`batch_embed_questions_task`、`reindex_all_questions_task` | 管理端上传/重建索引触发 |
   | `external_data_tasks.py` | `sync_external_jobs_task`（Greenhouse 职位）、`sync_codeforces_problems_task` | beat 每 6 小时 / 管理端手动 |
   | `email_tasks.py` | 邮件发送 | 注册验证等场景 |
   | `demo.py` | 演示任务 | beat 每 60 秒 |

3. `celery_worker.py`（后端根）— 本地启动 worker 的入口；对照 compose 里 `celery -A app.core.celery_app worker --loglevel=info`。
4. `app/services/backoffice/knowledge_service.py` 的入库编排 + `app/api/backoffice/v1/knowledge.py` — 看"上传即入队"的写法：API 只创建 `KnowledgeDocument` 记录并发任务，`status` 字段跟踪任务进度（管理端列表可见状态流转）。
5. `migrations/env.py` + 任选两个 `migrations/versions/*.py` 对照读，重点看含向量列和全文索引的迁移是怎么写的。
6. `app/route/route.py` 中的 metrics 中间件、安全头中间件、异常处理器（`APIException` 体系）；`app/common/log_consumer.py` 日志消费线程。

### 4.4 动手实践

1. **本地裸跑 worker**：在后端目录 `pip install -r requirements.txt` 后 `python celery_worker.py`（或 `celery -A app.core.celery_app worker -l info`），然后在管理端上传一份知识库文档，观察任务日志与 `knowledge_documents.status` 变化。
2. **Flower 监控**：`docker compose --profile monitoring up -d flower`，访问 `http://localhost:5555`，看任务队列、成功率、耗时。
3. **看 Redis 里的世界**：`docker compose exec redis redis-cli`，用 `KEYS *`（开发环境）看限流键、验证码键、Celery 队列键，分别对应哪段代码。
4. **写一个新任务**：仿照 `demo.py`，新增一个"每天统计面试总数并写日志"的 Celery 任务，注册到 `celery_app` 与 beat 计划，本地验证它被调度。
5. **做一次真实迁移**：给 `question_bank` 加一个 `note` 字段：改 model → `alembic revision --autogenerate -m "add note"` → 检查生成的迁移脚本 → `alembic upgrade head` → 进库验证。（做完记得回滚或撤销，保持仓库干净。）
6. **跑测试**：`pytest`（先跑 `test_smoke.py`，再跑 `test_security.py`），读懂每个断言在保护什么。

### 4.5 产出与检验标准

- [ ] 能画出"知识库文档上传"的异步全链路时序图（前端 → API → Celery 队列 → worker → DB 状态回写 → 前端轮询/刷新）。
- [ ] 能解释：为什么向量化必须放 Celery？如果 worker 挂了，上传的文档会是什么状态，如何补救？（提示：status 字段 + reindex 接口）
- [ ] 成功新增并运行一个自定义 Celery 任务、完成一次 Alembic 迁移。
- [ ] 能说出 Redis 在本项目中的四种用途及对应代码位置。
- [ ] `pytest` 全绿，并能解释 `test_agent_rag.py` 测了哪些点。

---

## 六、阶段五：容器化部署与进阶优化

> **建议周期**：1 周起（含综合实战）
> **阶段主题**：从"本地能跑"到"生产能部署"，再向架构师视角进阶。
> **配套必读**：`deployment-guide.md`（12KB，部署实操）。

### 5.1 学习目标

1. 吃透项目的容器化设计：多阶段/开发双 Dockerfile、组合式 compose、健康检查依赖链、Nginx 反代与 HTTPS。
2. 能独立完成一次真实部署（自有服务器/云主机）。
3. 建立优化清单意识：知道系统每个环节"还能怎么更好"，并有能力实施其中若干项。

### 5.2 源码精读路线

| # | 材料 | 关注点 |
| --- | --- | --- |
| 1 | `ai-interview-backend/Dockerfile` 与 `Dockerfile.dev` | 生产 vs 开发镜像差异；前端两个目录的 Dockerfile（容器内跑 Vite dev server + `VITE_PROXY_TARGET=http://app:8006`，体会容器网络内服务名寻址） |
| 2 | `ai-interview-backend/docker-compose.dev.yml` | 开发覆盖：暴露 8006、挂载源码热重载、禁用 nginx |
| 3 | `ai-interview-backend/nginx/nginx.conf` | 反代规则、`/uploads` 静态、HTTPS(8443) 与证书目录 `ssl/` |
| 4 | `scripts/deploy.sh` 与 `deployment-guide.md` | 真实部署步骤与注意事项 |
| 5 | `scripts/capture-current-ui.mjs` | Playwright 自动采集当前版本截图——"可验证的发布"思路 |

### 5.3 动手实践

1. **完整部署一次**：按 `deployment-guide.md` 把项目部署到一台服务器（或本机模拟生产：`ENV=production` + nginx），配置真实域名/自签证书走通 8443。
2. **生产化加固练习**：修改并验证——更换 `SECRET_KEY`、改数据库默认口令、设置 `CORS_ALLOW_ORIGINS` 为真实前端域名、观察生产下安全头（CSP/HSTS）生效。
3. **故障演练**（刻意制造问题再排查，最有价值的练习）：
   - 停掉 redis 容器 → 观察健康检查与限流行为（`RATE_LIMIT_FAIL_OPEN` 的两种表现）；
   - 把 `.env` 里 DashScope key 改错 → 走完一次上传文档，观察任务失败与状态呈现；
   - 用 `docker compose logs` + Flower + psql 三件套定位并恢复。
4. **截图流水线**：运行 `node scripts/capture-current-ui.mjs`，理解它如何登录管理端并采集截图。

### 5.4 进阶优化清单（选择 2~3 项实施）

| 方向 | 具体课题 | 入手位置 |
| --- | --- | --- |
| RAG 质量 | 用 `evaluate_rag.py` 建正式评估集，对比不同切分/重排策略；为知识库检索接专用 rerank 模型替代 LLM 重排 | `advanced_rag.py`、`scripts/evaluate_rag.py` |
| Agent | 给 `career_advisor` 输出增加结构化 schema 校验；把 scout 扇出数做成按岗位类目自适应 | `position_graph.py`、`state.py` |
| LLM 工程 | 给 `ai_service.py` 增加 token 用量统计与成本日志；评分输出做 schema 化校验替代正则剥离 | `ai_service.py`、`Interview.vue` |
| 性能 | 为 `question_bank.embedding` 建/调优 HNSW 索引并压测对比；embedding 批处理并发调优 | `embedding.py`、迁移脚本 |
| 可观测 | 接入 Prometheus + Grafana 看板；为 SSE 接口增加首字延迟指标 | `route.py` metrics 中间件 |
| 产品功能（综合实战） | **端到端二次开发命题**：新增"面试复盘错题本"——把用户回答得分低于阈值的题目自动收集，新增 model、迁移、backoffice/client 接口、前端页面。此题覆盖本路线图全部五层能力 | 全栈 |

### 5.5 产出与检验标准

- [ ] 独立完成一次含 Nginx/HTTPS 的生产部署，健康检查通过。
- [ ] 完成三项故障演练，并写出每次的"现象 → 定位路径 → 根因 → 修复"记录。
- [ ] 实施至少 2 项优化课题，提交可对比的前后数据（如评估集分数、查询延迟）。
- [ ] （综合）完成"错题本"功能：迁移、接口、前端页面、Docker 下全流程可用。
- [ ] 最终自测：合上电脑，能否向别人完整讲清楚这个系统的架构、数据流、关键设计取舍与已知短板？

---

## 七、附录

### 附录 A：核心文件地图速查表

| 模块 | 关键文件（相对各子项目根） |
| --- | --- |
| 应用工厂 | `ai-interview-backend/app/route/route.py`、`router_registry.py` |
| 配置 | `ai-interview-backend/app/core/config.py`、`.env.example` |
| 鉴权 | `app/core/security.py`、`app/api/client/deps.py`、`app/api/backoffice/deps.py` |
| AI 能力中枢 | `app/services/client/ai_service.py` |
| 面试业务 | `app/services/client/interview_service.py`、`app/api/client/v1/interview.py` |
| 简历业务 | `app/services/client/resume_service.py`、`app/api/client/v1/resume.py` |
| Agent 图 | `app/agents/position_graph.py`、`state.py`、`runtime.py`、`memory.py`、`setup_storage.py` |
| Agent 工具 | `app/services/client/position_agent_tools.py` |
| Embedding | `app/services/common/embedding.py` |
| RAG 融合/高级 | `app/services/common/rag.py`、`advanced_rag.py` |
| 知识库 | `app/services/backoffice/knowledge_service.py`、`app/api/backoffice/v1/knowledge.py` |
| 题库 | `app/services/backoffice/question_bank_service.py`、`app/api/backoffice/v1/question_bank.py` |
| Celery | `app/core/celery_app.py`、`app/schedule/jobs/*`、`celery_worker.py` |
| 数据模型 | `app/models/`（13 个模型）、`migrations/versions/` |
| 脚本 | `scripts/create_first_admin.py`、`seed_position_templates.py`、`evaluate_rag.py`、`deploy.sh` |
| 前端请求层 | `ai-interview-frontend/src/api/request.js`、`interview.js`（SSE） |
| 前端面试房 | `ai-interview-frontend/src/views/Interview.vue` |
| 管理端 API | `ai-interview-admin/src/api/index.js`（全部集中一个文件） |
| 部署 | 根 `docker-compose.yml`、`ai-interview-backend/docker-compose*.yml`、`nginx/nginx.conf` |

### 附录 B：常用调试命令

```bash
# 服务状态与日志
docker compose ps
docker compose logs -f app celery-worker

# 数据库（宿主机 5434）
docker compose exec postgres psql -U demo -d ai_interview

# Redis
docker compose exec redis redis-cli

# Celery
docker compose exec celery-worker celery -A app.core.celery_app inspect active
docker compose --profile monitoring up -d flower   # http://localhost:5555

# 迁移
docker compose exec app alembic current
docker compose exec app alembic upgrade head

# 测试
docker compose exec app pytest

# 截图采集
node scripts/capture-current-ui.mjs
```

### 附录 C：仓库文档索引（何时读）

| 文档 | 建议阅读时机 |
| --- | --- |
| `README.md` | 阶段一 |
| `docs/model-and-data-import-guide.md` | 阶段一（环境与数据准备） |
| `rag-implementation.md` | 阶段三 B（自己读完代码后对照） |
| `deployment-guide.md` | 阶段五 |
| `project-q-and-a.md` | 各阶段自查时当题库用 |
| `interview-notes.md`、`ai-application-engineering.md`、`engineering-capabilities.md` | 全部学完后，用于复盘与对外表达（面试/汇报） |

### 附录 D：常见问题预案

| 现象 | 排查方向 |
| --- | --- |
| 健康检查挂（PG/Redis 红） | `docker compose ps` 看依赖容器；确认 5434/6382 未被占用 |
| 上传文档一直 pending | worker 是否在跑（`logs -f celery-worker`）；DashScope key 是否正确 |
| 面试发起报"题库不足" | 题库量太少或 `QUESTION_BANK_MIN_SCORE` 过高；先导入示例题库 |
| 前端 401 反复跳登录 | token 过期且 refresh 失败；检查 `request.js` 拦截器与后端时钟 |
| Agent match 超时 | LLM 调用慢属正常（前端给了 3 分钟超时）；查 `LLM_TIMEOUT_SECONDS` 与网络 |
| 向量检索分数普遍偏低 | query 与入库文本语言/措辞差异；尝试 `hybrid`/`advanced` 模式 |

---

> **最后一句话**：这条路线的终点不是"读完代码"，而是——当别人问"如果让你给这个系统加一个视频面试功能，你会怎么改"时，你能准确说出要动哪些层、哪些文件、哪些配置，以及为什么。
