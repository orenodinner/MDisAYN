from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError


class ActionItem(BaseModel):
    what: str
    who: Optional[str] = None
    due: Optional[str] = None
    evidence: Optional[str] = None


class EntityItem(BaseModel):
    type: str
    value: str


class LLMResult(BaseModel):
    title: str
    summary: List[str]
    decisions: List[str]
    actions: List[ActionItem]
    entities: List[EntityItem]
    tags: List[str]
    projects: List[str]
    people: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _coerce_actions(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _coerce_entities(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def normalize_llm_payload(data: Dict[str, Any]) -> LLMResult:
    actions_payload = []
    for item in _coerce_actions(data.get("actions")):
        actions_payload.append(
            {
                "what": str(item.get("what") or "unspecified"),
                "who": item.get("who"),
                "due": item.get("due"),
                "evidence": item.get("evidence"),
            }
        )

    entities_payload = []
    for item in _coerce_entities(data.get("entities")):
        entities_payload.append(
            {
                "type": str(item.get("type") or "other"),
                "value": str(item.get("value") or ""),
            }
        )

    payload = {
        "title": str(data.get("title", "")) or "Untitled",
        "summary": _coerce_list(data.get("summary")),
        "decisions": _coerce_list(data.get("decisions")),
        "actions": actions_payload,
        "entities": entities_payload,
        "tags": _coerce_list(data.get("tags")),
        "projects": _coerce_list(data.get("projects")),
        "people": _coerce_list(data.get("people")),
        "confidence": float(data.get("confidence", 0.5)),
    }
    try:
        return LLMResult(**payload)
    except ValidationError:
        payload["confidence"] = max(0.0, min(1.0, payload.get("confidence", 0.5)))
        return LLMResult(**payload)


def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None
