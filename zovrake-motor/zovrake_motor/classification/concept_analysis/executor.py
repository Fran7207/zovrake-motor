"""Ejecutor de detectores del Concept Analysis Engine."""

from __future__ import annotations

from zovrake_motor.classification.concept_analysis.catalog import ConceptCatalogBuilder
from zovrake_motor.classification.concept_analysis.enums import ConceptAnalysisStatus
from zovrake_motor.classification.concept_analysis.gateway import InternalModelView
from zovrake_motor.classification.concept_analysis.models import (
    ConceptAnalysisIncident,
    ConceptAnalysisResult,
    ConceptCandidate,
)
from zovrake_motor.classification.concept_analysis.registry import ConceptDetectorRegistry
from zovrake_motor.config.categories.classification import ConceptAnalysisSettings


class ConceptAnalysisExecutor:
    """Coordina la ejecución secuencial de detectores sin modificar el modelo interno."""

    def __init__(
        self,
        registry: ConceptDetectorRegistry,
        *,
        catalog_builder: ConceptCatalogBuilder | None = None,
    ) -> None:
        self._registry = registry
        self._catalog_builder = catalog_builder or ConceptCatalogBuilder()

    def execute(
        self,
        model_view: InternalModelView,
        *,
        settings: ConceptAnalysisSettings,
    ) -> ConceptAnalysisResult:
        concepts: list[ConceptCandidate] = []
        incidents: list[ConceptAnalysisIncident] = []
        observations: list[str] = []
        sequence = 1

        for detector in self._registry.all_detectors():
            result = detector.detect(model_view, start_sequence=sequence)
            concepts.extend(result.concepts)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.concepts)

        if len(concepts) > settings.max_concepts_per_process:
            incidents.append(
                ConceptAnalysisIncident(
                    detector_name="concept_analysis_executor",
                    message=(
                        f"Se identificaron {len(concepts)} conceptos; "
                        f"límite configurado: {settings.max_concepts_per_process}"
                    ),
                    severity="warning",
                ),
            )
            concepts = concepts[: settings.max_concepts_per_process]

        catalog = self._catalog_builder.build(
            model_view=model_view,
            concepts=tuple(concepts),
            material_classification_prepared=settings.material_classification_prepared,
            service_classification_prepared=settings.service_classification_prepared,
            normalization_prepared=settings.normalization_prepared,
        )

        status = ConceptAnalysisStatus.IDENTIFIED if concepts else ConceptAnalysisStatus.SKIPPED
        observations.extend(
            (
                "internal_model_preserved=True",
                "canonical_representation_unmodified=True",
                "original_document_unaccessed=True",
                f"concepts_identified={len(concepts)}",
            ),
        )

        return ConceptAnalysisResult(
            process_id=model_view.process_id,
            document_id=model_view.document_id,
            model_id=model_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            internal_model_preserved=True,
            detectors_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
