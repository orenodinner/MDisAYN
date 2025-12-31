from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def _bullets(items: List[str], fallback: str = "(none)") -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def _actions(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "- [ ] (none)"
    lines = []
    for item in items:
        what = item.get("what") or "(unspecified)"
        who = item.get("who") or ""
        due = item.get("due") or ""
        evidence = item.get("evidence") or ""
        meta = ", ".join(part for part in [who, due, evidence] if part)
        if meta:
            lines.append(f"- [ ] {what} ({meta})")
        else:
            lines.append(f"- [ ] {what}")
    return "\n".join(lines)


def render_source_card(
    payload: Dict[str, Any],
    source_links: List[str],
    source_type: str,
    created_at: datetime,
    entities: List[Dict[str, Any]],
) -> str:
    title = payload.get("title") or "Untitled"
    summary = payload.get("summary", [])
    decisions = payload.get("decisions", [])
    actions = payload.get("actions", [])
    tags = payload.get("tags", [])
    projects = payload.get("projects", [])
    people = payload.get("people", [])
    confidence = payload.get("confidence", 0.0)

    entities_lines = []
    for entity in entities:
        etype = entity.get("type", "other")
        value = entity.get("value", "")
        if value:
            entities_lines.append(f"- {etype}: {value}")
    entities_block = "\n".join(entities_lines) if entities_lines else "- (none)"

    tags_block = " ".join(f"#{tag}" for tag in tags) if tags else "(none)"

    links_block = "\n".join(f"- {link}" for link in source_links) if source_links else "- (none)"

    return (
        f"# {title}\n\n"
        f"- Source: {source_type}\n"
        f"- Ingested: {created_at.isoformat()}\n"
        f"- Confidence: {confidence}\n\n"
        "## 原本リンク\n"
        f"{links_block}\n\n"
        "## 要点\n"
        f"{_bullets(summary)}\n\n"
        "## 決定事項\n"
        f"{_bullets(decisions)}\n\n"
        "## 次アクション\n"
        f"{_actions(actions)}\n\n"
        "## タグ/人物/プロジェクト\n"
        f"- Tags: {tags_block}\n"
        f"- People: {', '.join(people) if people else '(none)'}\n"
        f"- Projects: {', '.join(projects) if projects else '(none)'}\n"
        f"- Entities:\n{entities_block}\n"
    )
