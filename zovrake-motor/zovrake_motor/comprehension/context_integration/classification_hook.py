"""Punto de integración preparado para Clasificación Inteligente (PM5)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.context_integration.models import ContextAssociation
from zovrake_motor.config.categories.comprehension import DocumentContextIntegrationSettings


class ClassificationContextPoint:
    """
    Punto de integración para el Módulo de Clasificación Inteligente.

    Prepara el contexto para consumo futuro sin interpretarlo.
    """

    def __init__(self, *, settings: DocumentContextIntegrationSettings | None = None) -> None:
        self._settings = settings or DocumentContextIntegrationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.classification_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.classification_enabled

    def can_execute(self) -> bool:
        return self.is_prepared and self.is_enabled

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "classification_enabled": self.is_enabled,
            "can_execute": self.can_execute(),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_for_future_classification(self, association: ContextAssociation) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Clasificación preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
            "context_id": association.traceability.context_id,
            "document_id": association.traceability.document_id,
            "model_reference": association.model_reference,
        }
