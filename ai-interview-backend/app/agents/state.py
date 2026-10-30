"""Typed state shared by the position matching graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, NotRequired, TypedDict


class PositionAgentState(TypedDict, total=False):
    user_id: int
    resume_id: int
    target_direction: str | None
    parsed_resume: dict[str, Any]
    profile: dict[str, Any]
    memory: dict[str, Any]
    scout_category: str | None
    scout_results: Annotated[list[dict[str, Any]], operator.add]
    recommended_positions: list[dict[str, Any]]
    top_position_focus: dict[str, Any]
    next_actions: list[str]
    result: dict[str, Any]
    completed_steps: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
    run_id: str
    input_version: NotRequired[str]
