from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from .normalize import normalize_llm_payload, parse_json_from_text


class LLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_sec: float,
        max_retries: int,
        language: str = "ja",
        use_json_mode: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.language = language
        self.use_json_mode = use_json_mode

    def _chat(self, messages: list[dict[str, str]], json_mode: bool = False) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        with httpx.Client(timeout=self.timeout_sec) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

    def normalize(self, text: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = (
            "You are a structured data extractor. "
            "You MUST output valid JSON based on the provided schema."
        )
        schema = {
            "title": "string",
            "summary": ["string"],
            "decisions": ["string"],
            "actions": [
                {"what": "string", "who": "string|null", "due": "YYYY-MM-DD|null", "evidence": "string|null"}
            ],
            "entities": [{"type": "person|org|product|place|other", "value": "string"}],
            "tags": ["string"],
            "projects": ["string"],
            "people": ["string"],
            "confidence": 0.0,
        }
        language_hint = (
            "Output content MUST be in Japanese unless the source is clearly another language."
            if self.language.lower().startswith("ja")
            else f"Output content MUST be in {self.language}."
        )
        base_user_prompt = (
            "Normalize the input into the JSON schema below."
            "\nSchema:\n"
            f"{json.dumps(schema, ensure_ascii=True)}"
            "\nSource metadata:\n"
            f"{json.dumps(source_info, ensure_ascii=True)}"
            "\nLanguage:\n"
            f"{language_hint}"
            "\nInput:\n"
            f"{text}"
        )

        prompt = base_user_prompt
        last_error = None
        for attempt in range(self.max_retries + 1):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            response_text = self._chat(messages, json_mode=self.use_json_mode)
            if self.use_json_mode:
                try:
                    payload = json.loads(response_text)
                except json.JSONDecodeError:
                    payload = parse_json_from_text(response_text)
            else:
                payload = parse_json_from_text(response_text)
            if payload is None:
                last_error = "invalid_json"
            else:
                try:
                    result = normalize_llm_payload(payload)
                    return result.model_dump()
                except Exception:
                    last_error = "schema_validation_failed"

            prompt = (
                "Fix the JSON to be valid and match the schema. Return JSON only.\n"
                f"Original response:\n{response_text}"
            )

        raise RuntimeError(f"LLM normalization failed: {last_error}")
