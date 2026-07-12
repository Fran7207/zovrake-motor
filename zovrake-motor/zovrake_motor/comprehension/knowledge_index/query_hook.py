"""Punto de integración preparado para consultas futuras."""

from __future__ import annotations

from typing import Any

from zovrake_motor.config.categories.comprehension import DocumentKnowledgeIndexSettings


class QueryIntegrationPoint:
    """
    Punto de integración para motor de consultas futuro.

    No ejecuta consultas en esta etapa — únicamente prepara la arquitectura.
    """

    SUPPORTED_CRITERIA = ("document_id", "provider_name", "project_id", "requirement_code", "model_id")

    def __init__(self, *, settings: DocumentKnowledgeIndexSettings | None = None) -> None:
        self._settings = settings or DocumentKnowledgeIndexSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.query_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.query_enabled

    def can_execute(self) -> bool:
        return self.is_prepared and self.is_enabled

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "query_enabled": self.is_enabled,
            "can_execute": self.can_execute(),
            "supported_criteria": list(self.SUPPORTED_CRITERIA),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_for_future_queries(self, *, query_keys: dict[str, str]) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Consultas preparadas — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
            "available_keys": list(query_keys.keys()),
        }
