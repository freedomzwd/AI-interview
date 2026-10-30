# 上下文压缩策略设计

> 面向 AI-Interview 智能面试系统。本文只给方案，不改动现有源码。
> 结论先行：项目当前**没有上下文压缩机制**，只有一处 `chat_history[-6:]` 硬截断。
> 真正的上下文风险不在面试对话链路（容量充裕），而在 LangGraph state 的累加驻留。

---

## 1. 现状诊断

### 1.1 两条 LLM 链路

| 链路 | 入口 | 上下文形态 | 是否有压缩 |
|---|---|---|---|
| 面试对话 | `InterviewService.submit_answer[_stream]` → `AIService.evaluate_answer[_stream]` | 对话历史 + 简历 JSON + 当前题 | 仅 `[-6:]` 硬截断 |
| 岗位匹配 Agent | `PositionAgentService.run_agent` → LangGraph `position-match` | 结构化 state + checkpoint | 无，且 state 只增不减 |

前置环节（出题、简历解析、报告生成）均是单次调用，不构成历史累积，不在本文范围。

### 1.2 具体问题清单

| # | 位置 | 问题 | 影响 |
|---|---|---|---|
| P1 | `app/services/client/ai_service.py:371`、`:429` | `chat_history[-6:]`，按消息条数硬切 | 10 题面试从第 4 题起，前 3 题永久丢失；跨题一致性判断失去依据 |
| P2 | 同上 | 按条数而非按轮次切分 | 流式路径拿到的是 `flush` 前的消息快照，可能切出「有问无答」的半轮，模型会把残缺对话当完整历史 |
| P3 | `ai_service.py:401`、`:454` | 每轮 `json.dumps(resume_context)` 全量重传 | 简历 JSON 通常 1.5–4k 字，10 题累计传输量呈 O(n²) 增长 |
| P4 | `interview_service.py:210-215`、`:366-371` | 每次从 DB 拉取该场全部消息，再到下游才截断 | DB → 内存 → 序列化的无效搬运随题数线性增长 |
| P5 | `app/agents/state.py:17` | `scout_results: Annotated[list, operator.add]` | reducer 只追加不回收，每个 scout 的完整结果永久驻留 state |
| P6 | `app/agents/position_graph.py:126-129` | scout 返回含 JD 全文的完整岗位对象 | 3 分支 × 5 岗位，`merge_positions` 只用前 3 条，其余成为死数据 |
| P7 | `app/services/client/position_agent_service.py:17` | `thread_id` 内嵌 `uuid4` | 每次 run 生成新 thread，checkpoint 表无限增长，无 TTL |
| P8 | `app/core/config.py` 全局 | 无 token 计量、无预算配置、无触发阈值 | 上下文容量完全依赖 `max_tokens=2000` 的输出侧限制兜底 |

### 1.3 一个必须先纠正的判断

当前题量下**不存在窗口溢出风险**：10 题 × 每题约 1500 字 ≈ 20k token，DeepSeek 上下文为 128k。

因此压缩的目标不是「防止爆窗」，而是：

1. **成本与延迟**：把每轮重复传输的固定开销（简历全文）降为一次性卡片，总 token 从 O(n²) 降为 O(n)。
2. **评分一致性**：减少无关历史噪声，避免早期内容缺失导致的评分漂移。
3. **Agent 侧数据卫生**：state 与 checkpoint 不随运行次数膨胀。

按「窗口要满了才压缩」的思路设计，会得出错误方案（例如激进摘要、丢弃中段），反而损害面试质量。

---

## 2. 设计原则

1. **信息不丢，只降分辨率。** 任何被移出窗口的内容必须先进入摘要，禁止直接丢弃。
2. **摘要要有 schema。** 面试场景的核心信号是「答错了什么 / 埋了什么伏笔 / 哪里前后矛盾」，自由摘要必然丢失这些。必须用固定字段约束输出。
3. **压缩必须幂等。** 记录已摘要到的位置锚点，重试和并发不得重复压缩同一段内容。
4. **压缩失败不阻塞主流程。** 面试是实时交互，摘要超时应降级为纯窗口模式，而不是让用户等待或报错。
5. **每一层可独立上线。** L0 计量、L1 裁剪、L2 摘要、L3 state 收敛互不依赖，可分四次提交。

---

## 3. 分层方案

### L0 · 计量层（必做前置）

不引入 `tiktoken`：DeepSeek 使用自有 tokenizer，BPE 估算偏差常在 20% 以上，且给部署增加依赖。采用字符类别加权估算，误差可接受且零依赖。

```python
# app/agents/context_budget.py
import re

_CJK = re.compile(r"[\u4e00-\u9fff]")


def estimate_tokens(text: str) -> int:
    """按字符类别加权估算 token 数。中文 0.65 tok/字，其余 4 字符/tok。"""
    if not text:
        return 0
    cjk = len(_CJK.findall(text))
    return int(cjk * 0.65 + (len(text) - cjk) / 4) + 1
```

预算按区划分，各区配额独立，超配额时只调整本区：

| 区 | 内容 | 配额（token） | 超限处理 |
|---|---|---|---|
| system | 评分指令 + 输出格式 | 300 | 固定，不参与压缩 |
| candidate_card | 候选人卡 | 400 | 生成阶段硬截断 |
| summary | 摘要区 | 600 | 摘要 prompt 内限制字数 |
| recent_turns | 最近 K 轮原文 | 1400 | 减少 K，溢出部分进摘要 |
| current | 当前题 + 采分点 + 参考答案 | 800 | 采分点取前 8 条 |
| **合计** | | **3500** | 超出即触发压缩 |

### L1 · 结构化裁剪层

**L1-a 候选人卡。** 简历只在首次出题时用全文，之后改用压缩卡片。复用现有 `AIService._chat_json` 的校验与降级机制即可。

```python
# app/schemas/ai.py 新增
class CandidateCard(BaseModel):
    level: str = ""
    primary_stack: list[str] = []
    highlight_projects: list[str] = []   # 每条含「项目 + 技术点 + 量化结果」
    weak_points: list[str] = []
```

落库：`resumes` 表新增 `summary_card TEXT`，随解析任务一次性生成（`app/schedule/jobs/` 已有异步解析链路，挂进去即可）。

**L1-b 轮次对齐窗口。** 消息按 `question_index` 分组，取最后 K 组，保证窗口首条一定是 `interviewer`。

```python
def build_turns(messages: list) -> list[dict]:
    """按 question_index 聚合成轮次，避免切出有问无答的半轮。"""
    turns: dict[int, dict] = {}
    for m in messages:
        idx = m.question_index if m.question_index is not None else -1
        slot = turns.setdefault(idx, {"index": idx, "question": "", "answer": ""})
        if m.role == "interviewer":
            slot["question"] = m.content
        else:
            slot["answer"] = m.content
    return [turns[k] for k in sorted(turns)]
```

### L2 · 滚动摘要层（核心）

#### 3.2.1 数据结构

`interviews` 表新增两列，不加新表：

```sql
ALTER TABLE interviews ADD COLUMN context_summary TEXT;
ALTER TABLE interviews ADD COLUMN summary_upto_index INTEGER DEFAULT -1;
```

- `context_summary`：JSON 字符串，结构见 3.2.3
- `summary_upto_index`：已摘要到的 `question_index`，幂等锚点

#### 3.2.2 触发与装配流程

```python
async def build_eval_context(db, interview, current_index: int) -> str:
    card = await get_candidate_card(db, interview.resume_id)
    summary = json.loads(interview.context_summary) if interview.context_summary else {}
    turns = build_turns(await load_messages(db, interview.id))

    recent = turns[-RECENT_TURNS:]
    payload = render(card, summary, recent, interview.questions_data[current_index])

    if estimate_tokens(payload) <= BUDGET_TOTAL:
        return payload                      # 未超预算，零额外开销

    # 只压缩尚未摘要过的轮次，锚点之前的已固化
    anchor = interview.summary_upto_index if interview.summary_upto_index is not None else -1
    fresh = [t for t in turns if t["index"] > anchor]
    overflow = fresh[:-RECENT_TURNS]        # 从最新的 K 轮里扣掉，其余进摘要
    if not overflow:
        return payload                      # 无处可压，原样返回（宁可不压也不丢）

    try:
        summary = await summarize(prev=summary, dropped=overflow)
    except Exception:
        CTX_COMPRESS.labels(result="fallback").inc()
        return payload                      # 降级：不写库，本轮用纯窗口

    interview.context_summary = json.dumps(summary, ensure_ascii=False)
    interview.summary_upto_index = overflow[-1]["index"]
    await db.commit()
    CTX_COMPRESS.labels(result="success").inc()
    return render(card, summary, recent, interview.questions_data[current_index])
```

#### 3.2.3 摘要 prompt

```python
SUMMARY_PROMPT = """你是面试记录的压缩器。保留可复用于后续评分的关键信号。

已有摘要：
{prev}

待压缩轮次：
{rendered}

只返回 JSON，不要 markdown：
{{
  "covered_topics": ["已考察的技术主题"],
  "correct_points": ["候选人答对或答好的要点"],
  "weak_points": ["候选人答错、含糊或明显不会的点"],
  "open_threads": ["面试官提出但尚未追问深入的方向"],
  "contradictions": ["与其他轮次陈述冲突的内容，无则空数组"]
}}

约束：
- 每条不超过 30 字，总长不超过 {max_chars} 字
- 不评价性格、不给建议、不写分数
- 与已有摘要合并去重，同类归并而非追加"""
```

字段设计依据：通用对话摘要会输出「聊了项目经验、问了 Redis」这类平铺描述，对评分毫无用处。`weak_points` 和 `open_threads` 才决定了后续追问方向和报告质量；`contradictions` 是软技能评估的唯一线索来源。

#### 3.2.4 幂等保证

三个位置都可能重复触发压缩（用户重复提交、SSE 断流重试、Celery 重跑），必须依赖 `summary_upto_index` 单调递增来保证幂等：

- 只有 `index > summary_upto_index` 的轮次才参与压缩
- 写入与 `summary_upto_index` 更新在同一事务内提交
- 摘要内容按字段做集合归并（见 prompt 最后一条约束），即使重复压缩也不会指数膨胀

#### 3.2.5 失败降级

| 场景 | 处理 |
|---|---|
| 摘要 LLM 超时 / 报错 | 不写库，本轮用纯窗口，打 `result=fallback` 指标 |
| 摘要输出 JSON 校验失败 | 走 `_chat_json` 既有的一次修复逻辑，再失败则同上 |
| 溢出轮次为空 | 原样返回当前窗口，不做任何裁剪 |
| 并发压缩同一 interview | DB 行级锁（`SELECT ... FOR UPDATE`）或乐观锁比对 `summary_upto_index` |

### L3 · LangGraph state 收敛层

| 改动 | 位置 | 说明 |
|---|---|---|
| 移除 `operator.add` | `app/agents/state.py:17` | `scout_results` 改为普通 `list`，节点返回即覆盖；并行分支的结果由 `merge_positions` 统一归并 |
| scout 返回精简结构 | `position_agent_tools.py::match_positions` | 只返回 `position_tag / title / match_score / missing_skills`，JD 全文按需二次查询 |
| `parsed_resume` 外置 | `position_graph.py:111` | state 只存 `resume_id` 引用，原文放 Store，节点内按需读取 |
| checkpoint TTL 清理 | `app/schedule/jobs/` 新增任务 | 清理 `thread_id LIKE 'position-match:%'` 且创建超 7 天的 checkpoint |

注意：`operator.add` 在 LangGraph 中用于并行分支的 fan-in 归并，直接删除需要确认 `Send` 分支的结果仍能正确汇合。安全做法是保留 reducer，但把归并逻辑内联进 reducer 函数（去重 + 只留 top-N），使 channel 最大值受控而非随分支数累加。

---

## 4. 配置项

```python
# app/core/config.py 追加
CONTEXT_COMPRESSION_ENABLED: bool = False   # 灰度开关，便于 A/B
CONTEXT_BUDGET_TOTAL: int = 3500
CONTEXT_RECENT_TURNS: int = 3
CONTEXT_SUMMARY_MAX_CHARS: int = 500
CONTEXT_CARD_ENABLED: bool = True
AGENT_CHECKPOINT_TTL_DAYS: int = 7
```

## 5. 观测指标

沿用 `app/core/metrics.py` 现有风格：

```python
CTX_TOKENS = Histogram(
    "ai_interview_context_tokens", "Prompt tokens per LLM call", ("zone",)
)
CTX_COMPRESS = Counter(
    "ai_interview_context_compression_total", "Context compaction events", ("result",)
)
```

`zone` 取 `summary` / `recent_turns` / `card` / `total`，`result` 取 `success` / `fallback` / `skipped`。

需要盯的三条曲线：
- 单次调用 token 的 p50/p95 随题号的增长斜率（压缩生效后应接近水平）
- `compress_total{result="fallback"}` 占比（高于 5% 说明摘要调用不稳定）
- 摘要延迟 p95（应低于 2s，否则考虑移到异步）

## 6. 落地顺序与验收

| 阶段 | 内容 | 可独立上线 |
|---|---|---|
| 1 | L0 计量 + L1-b 轮次对齐窗口 | 是，零风险，先修 P2 |
| 2 | L1-a 候选人卡 | 是，需一次 `resumes` 迁移 |
| 3 | L2 滚动摘要 + 两列迁移 | 是，挂 `CONTEXT_COMPRESSION_ENABLED` |
| 4 | L3 state 收敛 + checkpoint TTL | 是，独立于前三阶段 |

**验收方法**：构造 20 份固定简历 × 每份 10 题的脚本化回答，A/B 对比三项指标：

1. 第 8 题时的 prompt token 数（预期下降 50% 以上）
2. 评分与人工标注的一致率（预期不劣化，劣化即说明摘要丢了关键信号）
3. 端到端 p95 延迟（摘要多一次 LLM 调用，可能上涨；若上涨超过 200ms，改为异步预生成——在返回上一题的「下一题」响应后再后台触发）

第 2 项是唯一不能妥协的指标。省下的 token 不能以评分质量为代价。

## 7. 为什么不用现成组件

| 组件 | 不适用原因 |
|---|---|
| `langchain_core.messages.trim_messages` | 只能按 token 裁剪，不能压缩；裁剪掉的内容不可恢复 |
| `ConversationSummaryBufferMemory` | langchain 0.1 起移出主路径，0.3 无维护 |
| LangMem `SummarizationNode` | 通用对话摘要，无领域 schema，`weak_points` / `contradictions` 必然丢失 |
| `MemorySaver` 自带清理 | 仅清内存态，Postgres checkpointer 仍需自行管理 TTL |

自研摘要器的实际增量只有两点：schema 约束 + 幂等锚点。但这两点恰好是该场景的全部价值。

## 8. 可对外表述的技术要点

1. **压缩的动机判断先于实现**：先证明场景缺什么（成本、一致性、数据卫生），再选方案。当前系统不缺容量，缺的是成本曲线和信号密度。
2. **摘要结构化而非自由生成**：把领域知识（面试评分依赖哪些信号）编码进 schema，这是通用组件替代不了的部分。
3. **幂等锚点是正确性前提**：多层重试环境（SSE 断流、Celery 重跑、用户重复提交）下，没有锚点的摘要必然重复压缩。
4. **降级优先于成功**：压缩是优化路径，主流程不能因优化失败而阻塞。
5. **量化验收**：A/B 三项指标，其中评分一致率是一票否决项。
