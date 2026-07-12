"""Punto de integración preparado para Clasificación Inteligente."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.config.categories.comprehension import DocumentCanonicalSettings


class ClassificationIntegrationPoint:
    """
    Punto de integración para el Módulo de Clasificación Inteligente (PM5).

    Prepara la Representación Canónica para consumo sin depender del documento original.
    """

    def __init__(self, *, settings: DocumentCanonicalSettings | None = None) -> None:
        self._settings = settings or DocumentCanonicalSettings.default()

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

    def prepare_for_future_consumption(self, representation: CanonicalDocument) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Clasificación preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
            "document_id": representation.traceability.document_id,
            "schema_version": representation.schema_version,
            "immutable": representation.immutable,
        }
