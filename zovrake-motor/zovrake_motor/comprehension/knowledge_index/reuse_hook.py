"""Punto de integración preparado para reutilización de modelos."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexEntry
from zovrake_motor.config.categories.comprehension import DocumentKnowledgeIndexSettings


class ReuseIntegrationPoint:
    """
    Punto de integración para reutilización de modelos documentales.

    Prepara localización y evitación de reprocesamientos futuros.
    """

    def __init__(self, *, settings: DocumentKnowledgeIndexSettings | None = None) -> None:
        self._settings = settings or DocumentKnowledgeIndexSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.reuse_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.reuse_enabled

    def can_execute(self) -> bool:
        return self.is_prepared and self.is_enabled

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "reuse_enabled": self.is_enabled,
            "can_execute": self.can_execute(),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_for_future_reuse(self, entry: DocumentIndexEntry) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Reutilización preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
            "index_id": entry.index_id,
            "model_reference": entry.model_reference,
            "document_id": entry.traceability.document_id,
        }
