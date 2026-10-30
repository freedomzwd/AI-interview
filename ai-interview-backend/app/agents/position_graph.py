"""State-driven, resumable position matching workflow."""

from __future__ import annotations

import json
import time
from typing import Any

from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.types import Send

from app.agents.state import PositionAgentState
from app.core.config import settings
from app.core.metrics import AGENT_NODE_LATENCY
from app.schemas.ai import CareerAdviceResult
from app.services.client.ai_service import AIService
from app.services.client.position_agent_tools import (
    build_candidate_profile,
    get_parsed_resume,
    get_position_interview_focus,
    match_positions,
)

TAG_CATEGORIES = {
    "python_backend": "backend",
    "java_backend": "backend",
    "vue_frontend": "frontend",
    "react_frontend": "frontend",
    "ai_application": "ai",
    "fullstack": "backend",
    "mobile_android": "mobile",
    "devops": "devops",
}


def _timed(name: str):
    def decorator(func):
        async def wrapped(state: PositionAgentState):
            started = time.perf_counter()
            try:
                return await func(state)
            finally:
                AGENT_NODE_LATENCY.labels(node=name).observe(time.perf_counter() - started)

        return wrapped

    return decorator


def _fallback_actions(positions: list[dict[str, Any]]) -> list[str]:
    if not positions:
        return ["补充目标岗位所需的项目经验后重新进行岗位匹配。"]
    top = positions[0]
    missing = top.get("missing_skills", [])
    actions = [f"优先准备 {top.get('title', '推荐岗位')} 的高频面试题。"]
    if missing:
        actions.append("围绕缺失技能完成一个可展示的小型项目：" + "、".join(missing[:3]))
    actions.append("根据推荐面试重点完成一次专项模拟面试并复盘评分。")
    return actions


def _scout_categories(state: PositionAgentState) -> list[Send]:
    target = state.get("target_direction")
    profile = state.get("profile", {})
    if target:
        return [Send("position_scout", {"profile": profile, "scout_category": None})]

    categories = []
    for tag in profile.get("position_hints", []):
        category = TAG_CATEGORIES.get(tag)
        if category and category not in categories:
            categories.append(category)
    if not categories:
        categories = ["backend", "frontend", "ai"]
    return [
        Send("position_scout", {"profile": profile, "scout_category": category})
        for category in categories[: settings.AGENT_MAX_PARALLEL_SCOUTS]
    ]


def build_position_graph(*, memory_service, context_pipeline, checkpointer, store, operations=None):
    operations = operations or {
        "get_resume": get_parsed_resume.ainvoke,
        "build_profile": build_candidate_profile.ainvoke,
        "match_positions": match_positions.ainvoke,
        "get_focus": get_position_interview_focus.ainvoke,
        "career_advice": AIService._chat_json,
    }
    graph = StateGraph(PositionAgentState)

    @_timed("load_context")
    async def load_context(state: PositionAgentState) -> dict[str, Any]:
        memory = await context_pipeline.load(state["user_id"])
        return {"memory": memory, "completed_steps": ["load_context"]}

    @_timed("resume_analyst")
    async def resume_analyst(state: PositionAgentState) -> dict[str, Any]:
        resume_data = await operations["get_resume"]({"resume_id": state["resume_id"]})
        if resume_data.get("error"):
            return {"errors": [resume_data["error"]], "completed_steps": ["resume_analyst"]}
        profile = await operations["build_profile"]({"parsed_resume": resume_data["parsed_resume"]})
        if profile.get("error"):
            return {
                "parsed_resume": resume_data["parsed_resume"],
                "profile": {},
                "errors": [profile["error"]],
                "completed_steps": ["resume_analyst"],
            }
        return {
            "parsed_resume": resume_data["parsed_resume"],
            "profile": profile,
            "completed_steps": ["resume_analyst"],
        }

    @_timed("position_scout")
    async def position_scout(state: PositionAgentState) -> dict[str, Any]:
        category = state.get("scout_category")
        result = await operations["match_positions"](
            {
                "candidate_profile": state.get("profile", {}),
                "top_n": 5,
                "categories": [category] if category else None,
            }
        )
        return {
            "scout_results": [result],
            "completed_steps": [f"position_scout:{category or 'targeted'}"],
        }

    @_timed("merge_positions")
    async def merge_positions(state: PositionAgentState) -> dict[str, Any]:
        deduplicated: dict[str, dict[str, Any]] = {}
        for scout in state.get("scout_results", []):
            for position in scout.get("recommended_positions", []):
                key = position.get("position_tag")
                if key and (
                    key not in deduplicated
                    or position.get("match_score", 0) > deduplicated[key].get("match_score", 0)
                ):
                    deduplicated[key] = position
        positions = sorted(deduplicated.values(), key=lambda item: item.get("match_score", 0), reverse=True)[:3]
        errors = [] if positions else ["未找到可匹配的岗位模板"]
        return {
            "recommended_positions": positions,
            "errors": errors,
            "completed_steps": ["merge_positions"],
        }

    @_timed("interview_planner")
    async def interview_planner(state: PositionAgentState) -> dict[str, Any]:
        positions = state.get("recommended_positions", [])
        if not positions:
            return {"top_position_focus": {}, "completed_steps": ["interview_planner"]}
        focus = await operations["get_focus"](
            {"position_tag": positions[0]["position_tag"]}
        )
        return {"top_position_focus": focus, "completed_steps": ["interview_planner"]}

    @_timed("career_advisor")
    async def career_advisor(state: PositionAgentState) -> dict[str, Any]:
        positions = state.get("recommended_positions", [])
        if not positions and state.get("errors"):
            return {
                "result": {"error": state["errors"][0]},
                "next_actions": [],
                "completed_steps": ["career_advisor"],
            }
        fallback = CareerAdviceResult(next_actions=_fallback_actions(positions))
        context = context_pipeline.prompt_context(state.get("memory", {}), state.get("target_direction"))
        model = await operations["career_advice"](
            [
                {
                    "role": "system",
                    "content": "你是职业发展顾问。只返回 JSON：{\"next_actions\":[\"具体行动\"]}。给出 3 条可执行建议。",
                },
                {
                    "role": "user",
                    "content": "候选人画像：" + json.dumps(state.get("profile", {}), ensure_ascii=False)
                    + "\n推荐岗位：" + json.dumps(positions, ensure_ascii=False)
                    + "\n面试重点：" + json.dumps(state.get("top_position_focus", {}), ensure_ascii=False)
                    + ("\n" + context if context else ""),
                },
            ],
            CareerAdviceResult,
            fallback.model_dump(),
            temperature=0.3,
        )
        result = {
            "candidate_profile": state.get("profile", {}),
            "recommended_positions": positions,
            "top_position_focus": state.get("top_position_focus", {}),
            "next_actions": model.next_actions[:3] or fallback.next_actions,
        }
        return {"next_actions": result["next_actions"], "result": result, "completed_steps": ["career_advisor"]}

    @_timed("memory_writer")
    async def memory_writer(state: PositionAgentState) -> dict[str, Any]:
        await memory_service.save_match(
            state["user_id"], state.get("profile", {}), state.get("recommended_positions", [])
        )
        return {"completed_steps": ["memory_writer"]}

    graph.add_node("load_context", load_context)
    graph.add_node("resume_analyst", resume_analyst)
    graph.add_node("position_scout", position_scout)
    graph.add_node("merge_positions", merge_positions)
    graph.add_node("interview_planner", interview_planner)
    graph.add_node("career_advisor", career_advisor)
    graph.add_node("memory_writer", memory_writer)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "resume_analyst")
    graph.add_conditional_edges("resume_analyst", _scout_categories)
    graph.add_edge("position_scout", "merge_positions")
    graph.add_edge("merge_positions", "interview_planner")
    graph.add_edge("interview_planner", "career_advisor")
    graph.add_edge("career_advisor", "memory_writer")
    graph.add_edge("memory_writer", END)
    return graph.compile(checkpointer=checkpointer, store=store, name="position-match")
