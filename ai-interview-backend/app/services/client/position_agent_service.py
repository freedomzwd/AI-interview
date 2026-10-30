"""Public service facade for the LangGraph position matching workflow."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.agents.runtime import agent_runtime
from app.core.metrics import AGENT_RUNS

logger = logging.getLogger(__name__)


class PositionAgentService:
    @staticmethod
    def _thread_id(user_id: int, resume_id: int, run_id: str) -> str:
        return f"position-match:{user_id}:{resume_id}:{run_id}"

    @staticmethod
    def _steps(state: dict) -> list[dict]:
        """Build user-facing, non-sensitive summaries of the graph execution."""
        profile = state.get("profile") or {}
        positions = state.get("recommended_positions") or []
        focus = state.get("top_position_focus") or {}
        primary_skills = profile.get("primary_stack") or []
        secondary_skills = profile.get("secondary_stack") or []
        position_titles = [item.get("title") for item in positions if item.get("title")]

        category_labels = {
            "ai": "AI 应用",
            "backend": "后端开发",
            "frontend": "前端开发",
            "mobile": "移动开发",
            "devops": "运维工程",
        }
        descriptions = {
            "load_context": ("加载匹配上下文", "已读取历史偏好，用于调整推荐优先级。", []),
            "resume_analyst": (
                "分析简历能力画像",
                "已识别候选人的核心技术栈与项目方向。",
                [f"核心技能：{', '.join(primary_skills[:5])}" if primary_skills else "已完成技能提取"],
            ),
            "merge_positions": (
                "归并岗位推荐",
                f"已从多个方向汇总并排序 {len(positions)} 个推荐岗位。",
                [f"优先推荐：{'、'.join(position_titles[:3])}" if position_titles else "未产生可展示岗位"],
            ),
            "interview_planner": (
                "制定面试练习计划",
                "已为首选岗位生成专项练习建议。",
                [f"练习重点：{'、'.join((focus.get('focus_topics') or [])[:4])}" if focus.get("focus_topics") else "已生成练习方向"],
            ),
            "career_advisor": ("生成下一步建议", "已结合岗位匹配结果生成行动建议。", []),
            "memory_writer": ("更新个人偏好", "已保存本次匹配摘要，用于后续推荐优化。", []),
        }

        steps = []
        for step in state.get("completed_steps", []):
            if step.startswith("position_scout:"):
                category = step.split(":", 1)[1]
                label = category_labels.get(category, category)
                title = f"检索{label}岗位"
                summary = f"已在{label}模板库中检索候选人适配的岗位。"
                highlights = [f"检索到 {len(positions)} 个可用推荐结果"]
            else:
                title, summary, highlights = descriptions.get(
                    step,
                    (step, "该步骤已完成。", []),
                )
            if step == "resume_analyst" and secondary_skills:
                highlights.append(f"补充技能：{', '.join(secondary_skills[:4])}")
            steps.append(
                {
                    "tool": step,
                    "title": title,
                    "summary": summary,
                    "highlights": highlights,
                    "input_preview": "",
                    "output_preview": "completed",
                }
            )
        return steps

    @classmethod
    async def run_agent(
        cls,
        *,
        user_id: int,
        resume_id: int,
        target_direction: str | None = None,
        run_id: str | None = None,
    ) -> dict:
        """Run or resume an isolated, checkpointed matching task."""
        run_id = run_id or str(uuid4())
        try:
            await agent_runtime.start()
            graph = agent_runtime.graph
            config = {
                "configurable": {
                    "thread_id": cls._thread_id(user_id, resume_id, run_id),
                }
            }
            snapshot = await graph.aget_state(config)
            values = dict(snapshot.values) if snapshot and snapshot.values else {}
            if values.get("result"):
                AGENT_RUNS.labels(status="reused").inc()
                return {
                    "run_id": run_id,
                    "result": values["result"],
                    "intermediate_steps": cls._steps(values),
                }

            if snapshot and snapshot.next:
                state = await graph.ainvoke(None, config=config)
            else:
                state = await graph.ainvoke(
                    {
                        "user_id": user_id,
                        "resume_id": resume_id,
                        "target_direction": target_direction,
                        "run_id": run_id,
                        "scout_results": [],
                        "completed_steps": [],
                        "errors": [],
                    },
                    config=config,
                )

            result = state.get("result")
            if not result:
                errors = state.get("errors", [])
                result = {"error": errors[0] if errors else "岗位匹配未生成结果"}
                AGENT_RUNS.labels(status="error").inc()
            else:
                AGENT_RUNS.labels(status="success").inc()
            return {
                "run_id": run_id,
                "result": result,
                "intermediate_steps": cls._steps(state),
            }
        except Exception as exc:
            logger.exception("LangGraph position matching failed")
            AGENT_RUNS.labels(status="error").inc()
            return {
                "run_id": run_id,
                "result": {"error": f"Agent 执行失败: {exc}"},
                "intermediate_steps": [],
            }
