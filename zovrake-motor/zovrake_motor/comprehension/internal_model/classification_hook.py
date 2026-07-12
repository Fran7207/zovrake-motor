"""Punto de integración preparado para Clasificación Inteligente (PM5)."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.internal_model.models import InternalDocumentModel
from zovrake_motor.config.categories.comprehension import DocumentInternalModelSettings


class ClassificationIntegrationPoint:
    """
    Punto de integración para el Módulo de Clasificación Inteligente.

    Prepara el Modelo Documental Interno para consumo sin depender
    del documento original ni de la Representación Canónica.
    """

    def __init__(self, *, settings: DocumentInternalModelSettings | None = None) -> None:
        self._settings = settings or DocumentInternalModelSettings.default()

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

    def prepare_for_future_consumption(self, model: InternalDocumentModel) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Clasificación preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
            "model_id": model.model_id,
            "document_id": model.document.document_id,
            "schema_version": model.schema_version,
            "immutable": model.immutable,
            "classification_ready": model.classification_ready,
        }
