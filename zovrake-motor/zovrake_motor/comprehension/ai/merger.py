"""Fusión no destructiva de comprensión local y OpenAI."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class AIUnderstandingMerger:
    def merge(
        self,
        *,
        local_understanding: dict[str, Any],
        ai_understanding: dict[str, Any],
    ) -> dict[str, Any]:
        result = deepcopy(local_understanding or {})
        result["hybrid_source"] = "local_plus_openai"
        result["ai_assisted"] = True
        result["ai_document_type"] = str(ai_understanding.get("document_type", ""))
        result["ai_summary"] = str(ai_understanding.get("summary", ""))
        for key in (
            "entities",
            "facts",
            "relationships",
            "sections",
            "items",
            "visual_observations",
            "numeric_checks",
            "uncertainties",
        ):
            result[f"ai_{key}"] = list(ai_understanding.get(key, ()) or ())
        result["ai_confidence"] = self._aggregate_confidence(ai_understanding)
        return result

    @staticmethod
    def _aggregate_confidence(payload: dict[str, Any]) -> float:
        values: list[float] = []
        for key in (
            "entities",
            "facts",
            "relationships",
            "sections",
            "items",
            "visual_observations",
            "numeric_checks",
        ):
            for item in payload.get(key, ()) or ():
                if isinstance(item, dict):
                    value = item.get("confidence")
                    if isinstance(value, (int, float)):
                        values.append(float(value))
        return round(sum(values) / len(values), 4) if values else 0.0
