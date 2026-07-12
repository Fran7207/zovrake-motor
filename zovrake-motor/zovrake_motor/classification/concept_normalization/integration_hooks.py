"""Puntos de integración preparados para motores posteriores del PM5."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_normalization.models import NormalizedConceptCatalog
from zovrake_motor.config.categories.classification import ConceptNormalizationSettings


class EquivalenceDetectionIntegrationPoint:
    """Prepara el catálogo normalizado para el Equivalence Detection Engine."""

    def __init__(self, *, settings: ConceptNormalizationSettings | None = None) -> None:
        self._settings = settings or ConceptNormalizationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.equivalence_detection_prepared

    def prepare_for_future_detection(self, catalog: NormalizedConceptCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Detección de equivalencias preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "concepts_count": len(catalog.concepts),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }


class ComparableGroupBuilderIntegrationPoint:
    """Prepara el catálogo normalizado para el Comparable Group Builder."""

    def __init__(self, *, settings: ConceptNormalizationSettings | None = None) -> None:
        self._settings = settings or ConceptNormalizationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comparable_group_builder_prepared

    def prepare_for_future_grouping(self, catalog: NormalizedConceptCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Construcción de grupos comparables preparada — sin ejecución en esta etapa",
            "integration_prepared": self.is_prepared,
            "catalog_id": catalog.catalog_id,
            "concepts_count": len(catalog.concepts),
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "integration_prepared": self.is_prepared,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
