from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader


def _wikilink(value: str) -> str:
    if not value:
        return ""
    return f"[[{value}]]"


@lru_cache(maxsize=8)
def _get_env(template_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["wikilink"] = _wikilink
    return env


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def render_source_card(
    payload: Dict[str, Any],
    source_links: List[str],
    source_type: str,
    created_at: datetime,
    entities: List[Dict[str, Any]],
    template_path: Path = Path("templates/source_card.md.j2"),
) -> str:
    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    env = _get_env(str(template_path.parent.resolve()))
    template = env.get_template(template_path.name)

    context = dict(payload)
    context.setdefault("title", "Untitled")
    context["summary"] = _ensure_list(context.get("summary"))
    context["decisions"] = _ensure_list(context.get("decisions"))
    context["actions"] = _ensure_list(context.get("actions"))
    context["tags"] = _ensure_list(context.get("tags"))
    context["projects"] = _ensure_list(context.get("projects"))
    context["people"] = _ensure_list(context.get("people"))

    context.update(
        {
            "source_links": source_links,
            "source_type": source_type,
            "created_at": created_at.isoformat(),
            "entities": entities,
        }
    )

    return template.render(context)
