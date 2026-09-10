"""Contratos de la capa de comprensión remota."""

from __future__ import annotations

from typing import Any, Protocol

from .models import AIComprehensionResult, ComprehensionRoute


class DocumentComprehensionProvider(Protocol):
    def comprehend(
        self,
        *,
        knowledge: Any,
        route: ComprehensionRoute,
        selected_context: dict[str, Any],
        pdf_bytes: bytes | None = None,
    ) -> AIComprehensionResult:
        ...
