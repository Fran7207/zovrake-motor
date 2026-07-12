"""Puntos de integración preparados para motores posteriores del PM5."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.context_association.models import ContextAssociationCatalog
from zovrake_motor.config.categories.classification import ContextAssociationSettings


class ComparativeDomainModelIntegrationPoint:
    """Prepara el catálogo de asociaciones para el Comparative Domain Model Builder."""

    def __init__(self, *, settings: ContextAssociationSettings | None = None) -> None:
        self._settings = settings or ContextAssociationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comparative_domain_model_prepared

    def prepare_for_future_modeling(self, catalog: ContextAssociationCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Modelo de dominio comparativo preparado — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "associations_count": len(catalog.associations),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
