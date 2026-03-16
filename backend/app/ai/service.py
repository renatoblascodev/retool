"""AI service — wraps LiteLLM for app generation and query suggestion."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
_TIMEOUT_SECONDS = 30


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text()


async def _call_llm(system_prompt: str, user_message: str) -> str:
    """Call LiteLLM with a timeout. Returns the text content of the response."""
    try:
        import litellm  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "litellm is not installed. Add 'litellm' to requirements.txt."
        ) from exc

    async def _completion() -> str:
        response = await litellm.acompletion(
            model=_AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    return await asyncio.wait_for(_completion(), timeout=_TIMEOUT_SECONDS)


async def generate_app(
    prompt: str,
    datasource_info: str = "No datasource selected.",
) -> dict:
    """
    Call the LLM to generate an app layout JSON.

    Returns the parsed JSON dict (matching GenerateAppResponse schema).
    Raises asyncio.TimeoutError on timeout, ValueError on invalid JSON/schema.
    """
    system_prompt = _load_prompt("generate_app.txt").format(
        datasource_info=datasource_info,
        user_prompt=prompt,
    )
    raw = await _call_llm(system_prompt, prompt)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned non-JSON for generate_app: %s", raw[:200])
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    if "layout" not in data:
        raise ValueError("LLM response missing required field 'layout'")

    return data


async def suggest_query(
    datasource_type: str,
    datasource_info: str,
    goal: str,
) -> dict:
    """
    Call the LLM to suggest a query for a given datasource and goal.

    Returns the parsed JSON dict (matching SuggestQueryResponse schema).
    """
    system_prompt = _load_prompt("suggest_query.txt").format(
        datasource_type=datasource_type,
        datasource_info=datasource_info,
        user_goal=goal,
    )
    raw = await _call_llm(system_prompt, goal)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned non-JSON for suggest_query: %s", raw[:200])
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    if "query" not in data or "explanation" not in data:
        raise ValueError("LLM response missing required fields 'query' or 'explanation'")

    return data
