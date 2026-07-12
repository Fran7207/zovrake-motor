"""Ejecutor de normalizadores del Concept Normalization Engine."""

from __future__ import annotations

from zovrake_motor.classification.concept_normalization.builders import build_normalized_concept_catalog
from zovrake_motor.classification.concept_normalization.enums import ConceptNormalizationStatus
from zovrake_motor.classification.concept_normalization.gateway import ClassificationCatalogView
from zovrake_motor.classification.concept_normalization.models import (
    ConceptNormalizationIncident,
    ConceptNormalizationResult,
    NormalizedConceptRecord,
)
from zovrake_motor.classification.concept_normalization.registry import ConceptNormalizerRegistry
from zovrake_motor.config.categories.classification import ConceptNormalizationSettings


class ConceptNormalizationExecutor:
    """Coordina la ejecución secuencial de normalizadores sin modificar catálogos de origen."""

    def __init__(self, registry: ConceptNormalizerRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: ClassificationCatalogView,
        *,
        settings: ConceptNormalizationSettings,
    ) -> ConceptNormalizationResult:
        concepts: list[NormalizedConceptRecord] = []
        incidents: list[ConceptNormalizationIncident] = []
        observations: list[str] = []
        sequence = 1

        for normalizer in self._registry.all_normalizers():
            result = normalizer.normalize(catalog_view, start_sequence=sequence)
            concepts.extend(result.concepts)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.concepts)

        if len(concepts) > settings.max_normalized_concepts_per_process:
            incidents.append(
                ConceptNormalizationIncident(
                    normalizer_name="concept_normalization_executor",
                    message=(
                        f"Se normalizaron {len(concepts)} conceptos; "
                        f"límite configurado: {settings.max_normalized_concepts_per_process}"
                    ),
                    severity="warning",
                ),
            )
            concepts = concepts[: settings.max_normalized_concepts_per_process]

        catalog = build_normalized_concept_catalog(
            catalog_view=catalog_view,
            concepts=tuple(concepts),
            equivalence_detection_prepared=settings.equivalence_detection_prepared,
            comparable_group_builder_prepared=settings.comparable_group_builder_prepared,
        )

        status = (
            ConceptNormalizationStatus.NORMALIZED if concepts else ConceptNormalizationStatus.SKIPPED
        )
        observations.extend(
            (
                "source_catalogs_preserved=True",
                "original_values_preserved=True",
                "original_document_unaccessed=True",
                f"concepts_normalized={len(concepts)}",
            ),
        )

        return ConceptNormalizationResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            source_catalogs_preserved=True,
            normalizers_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
