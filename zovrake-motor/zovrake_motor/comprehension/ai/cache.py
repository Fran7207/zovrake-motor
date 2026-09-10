"""Caché local para evitar repetir llamadas idénticas."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


class LocalAIComprehensionCache:
    def __init__(self, *, root: str | None = None) -> None:
        self.root = Path(
            root
            or os.getenv(
                "ZOVRAKE_OPENAI_CACHE_DIR",
                ".zovrake_cache/openai_comprehension",
            )
        )
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _canonical_context(context: dict[str, Any]) -> dict[str, Any]:
        """
        Reduce el tamaño de la llave: imágenes grandes se representan por su hash.
        """
        result = dict(context or {})
        images = []
        for item in result.get("selected_images", ()) or ():
            if not isinstance(item, dict):
                continue
            images.append(
                {
                    "page_number": item.get("page_number"),
                    "sha256": item.get("sha256", ""),
                    "detail": item.get("detail", "low"),
                }
            )
        result["selected_images"] = images
        return result

    def key(
        self,
        *,
        document_hash: str,
        route: str,
        model: str,
        selected_context: dict[str, Any],
    ) -> str:
        payload = {
            "document_hash": document_hash,
            "route": route,
            "model": model,
            "selected_context": self._canonical_context(selected_context),
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.root / f"{key}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        path = self.root / f"{key}.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        temp.replace(path)
