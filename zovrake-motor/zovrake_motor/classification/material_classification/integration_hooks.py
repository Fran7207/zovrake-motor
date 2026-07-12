"""Puntos de integración preparados para motores posteriores del PM5."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.material_classification.models import MaterialCatalog
from zovrake_motor.config.categories.classification import MaterialClassificationSettings


class ServiceClassificationIntegrationPoint:
    """Prepara el catálogo de materiales para el Service Classification Engine."""

    def __init__(self, *, settings: MaterialClassificationSettings | None = None) -> None:
        self._settings = settings or MaterialClassificationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.service_classification_prepared

    def prepare_for_future_classification(self, catalog: MaterialCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Clasificación de servicios preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "materials_count": len(catalog.materials),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }


class ConceptNormalizationIntegrationPoint:
    """Prepara el catálogo de materiales para el Concept Normalization Engine."""

    def __init__(self, *, settings: MaterialClassificationSettings | None = None) -> None:
        self._settings = settings or MaterialClassificationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.normalization_prepared

    def prepare_for_future_normalization(self, catalog: MaterialCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Normalización conceptual preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "materials_count": len(catalog.materials),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }


class EquivalenceDetectionIntegrationPoint:
    """Prepara el catálogo de materiales para el Equivalence Detection Engine."""

    def __init__(self, *, settings: MaterialClassificationSettings | None = None) -> None:
        self._settings = settings or MaterialClassificationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.equivalence_detection_prepared

    def prepare_for_future_detection(self, catalog: MaterialCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Detección de equivalencias preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "materials_count": len(catalog.materials),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }


class ComparableGroupBuilderIntegrationPoint:
    """Prepara el catálogo de materiales para el Comparable Group Builder."""

    def __init__(self, *, settings: MaterialClassificationSettings | None = None) -> None:
        self._settings = settings or MaterialClassificationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comparable_group_builder_prepared

    def prepare_for_future_grouping(self, catalog: MaterialCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Construcción de grupos comparables preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "materials_count": len(catalog.materials),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
