"""Puntos de integración preparados para motores posteriores del PM5."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_analysis.models import ConceptCatalog
from zovrake_motor.config.categories.classification import ConceptAnalysisSettings


class MaterialClassificationIntegrationPoint:
    """Prepara el catálogo para el Material Classification Engine (MCE)."""

    def __init__(self, *, settings: ConceptAnalysisSettings | None = None) -> None:
        self._settings = settings or ConceptAnalysisSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.material_classification_prepared

    def prepare_for_future_classification(self, catalog: ConceptCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Clasificación de materiales preparada — sin ejecución en esta etapa",
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


class ServiceClassificationIntegrationPoint:
    """Prepara el catálogo para el Service Classification Engine (SCE)."""

    def __init__(self, *, settings: ConceptAnalysisSettings | None = None) -> None:
        self._settings = settings or ConceptAnalysisSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.service_classification_prepared

    def prepare_for_future_classification(self, catalog: ConceptCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Clasificación de servicios preparada — sin ejecución en esta etapa",
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


class ConceptNormalizationIntegrationPoint:
    """Prepara el catálogo para el Concept Normalization Engine."""

    def __init__(self, *, settings: ConceptAnalysisSettings | None = None) -> None:
        self._settings = settings or ConceptAnalysisSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.normalization_prepared

    def prepare_for_future_normalization(self, catalog: ConceptCatalog) -> dict[str, Any]:
        return {
            "executed": False,
            "message": "Normalización conceptual preparada — sin ejecución en esta etapa",
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
