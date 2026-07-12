"""Puntos de integración preparados para motores posteriores del PM5."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.equivalence_detection.models import EquivalenceCatalog
from zovrake_motor.config.categories.classification import EquivalenceDetectionSettings


class ComparableGroupBuilderIntegrationPoint:
    """Prepara el catálogo de equivalencias para el Comparable Group Builder."""

    def __init__(self, *, settings: EquivalenceDetectionSettings | None = None) -> None:
        self._settings = settings or EquivalenceDetectionSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comparable_group_builder_prepared

    def prepare_for_future_grouping(self, catalog: EquivalenceCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Construcción de grupos comparables preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "equivalences_count": len(catalog.equivalences),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }


class ContextAssociationIntegrationPoint:
    """Prepara el catálogo de equivalencias para el Context Association Engine."""

    def __init__(self, *, settings: EquivalenceDetectionSettings | None = None) -> None:
        self._settings = settings or EquivalenceDetectionSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.context_association_prepared

    def prepare_for_future_association(self, catalog: EquivalenceCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Asociación de contexto preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "equivalences_count": len(catalog.equivalences),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }


class ComparativeDomainModelIntegrationPoint:
    """Prepara el catálogo de equivalencias para el Comparative Domain Model Builder."""

    def __init__(self, *, settings: EquivalenceDetectionSettings | None = None) -> None:
        self._settings = settings or EquivalenceDetectionSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comparative_domain_model_prepared

    def prepare_for_future_modeling(self, catalog: EquivalenceCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Modelo de dominio comparativo preparado — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "equivalences_count": len(catalog.equivalences),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
