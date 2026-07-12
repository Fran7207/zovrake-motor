"""Catálogo temporal en memoria de conceptos identificados."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_analysis.gateway import InternalModelView
from zovrake_motor.classification.concept_analysis.models import ConceptCandidate, ConceptCatalog


class TemporaryConceptCatalogStore:
    """
    Almacén temporal del catálogo de conceptos.

    Sin persistencia — preparado para consultas futuras dentro del proceso.
    """

    def __init__(self) -> None:
        self._catalogs: dict[str, ConceptCatalog] = {}

    def save(self, catalog: ConceptCatalog) -> None:
        self._catalogs[catalog.catalog_id] = catalog

    def get(self, catalog_id: str) -> ConceptCatalog | None:
        return self._catalogs.get(catalog_id)

    def get_by_process(self, process_id: UUID) -> ConceptCatalog | None:
        for catalog in self._catalogs.values():
            if catalog.process_id == process_id:
                return catalog
        return None

    def count(self) -> int:
        return len(self._catalogs)

    def snapshot(self) -> list[dict[str, Any]]:
        return [catalog.to_dict() for catalog in self._catalogs.values()]


class ConceptCatalogBuilder:
    """Construye el catálogo temporal uniforme a partir de conceptos detectados."""

    def build(
        self,
        *,
        model_view: InternalModelView,
        concepts: tuple[ConceptCandidate, ...],
        material_classification_prepared: bool,
        service_classification_prepared: bool,
        normalization_prepared: bool,
    ) -> ConceptCatalog:
        catalog_id = f"cae-catalog://{model_view.model_id}"
        return ConceptCatalog(
            catalog_id=catalog_id,
            process_id=model_view.process_id,
            model_id=model_view.model_id,
            document_id=model_view.document_id,
            concepts=concepts,
            material_classification_prepared=material_classification_prepared,
            service_classification_prepared=service_classification_prepared,
            normalization_prepared=normalization_prepared,
        )
