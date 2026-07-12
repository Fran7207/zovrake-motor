"""Punto de asociación con el Document Knowledge Index."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.context_integration.models import ContextAssociation
from zovrake_motor.config.categories.comprehension import DocumentContextIntegrationSettings


class DkiAssociationPoint:
    """
    Registra la asociación entre contexto e índice documental.

    No modifica el contenido del índice documental.
    """

    def __init__(self, *, settings: DocumentContextIntegrationSettings | None = None) -> None:
        self._settings = settings or DocumentContextIntegrationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.dki_association_prepared

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "modifies_index_content": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def register_association(self, association: ContextAssociation) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Asociación DKI registrada — sin modificar contenido del índice",
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
            "index_id": association.traceability.index_id,
            "context_id": association.traceability.context_id,
            "index_modified": False,
        }
