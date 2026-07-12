"""Ensamblador de la Representación Canónica."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.models import (
    CanonicalDocument,
    CanonicalRepresentationResult,
    CanonicalTraceability,
    SectionTransformationResult,
    TransformationIncident,
)
from zovrake_motor.comprehension.canonical.registry import TransformerRegistry
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class CanonicalAssembler:
    """
    Ensambla la Representación Canónica uniforme a partir de transformadores.

    No interpreta el contenido ni modifica el documento original.
    """

    def __init__(self, registry: TransformerRegistry) -> None:
        self._registry = registry

    def assemble(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
        classification_integration_prepared: bool,
    ) -> CanonicalRepresentationResult:
        section_results: list[SectionTransformationResult] = []
        incidents: list[TransformationIncident] = []
        observations: list[str] = []

        for transformer in self._registry.all_transformers():
            section_result = transformer.transform(extraction_result, traceability=traceability)
            section_results.append(section_result)
            observations.extend(section_result.technical_observations)
            incidents.extend(section_result.incidents)

        provider = self._registry.get_provider_transformer().build_provider(
            extraction_result,
            traceability=traceability,
        )
        commercial_information = self._registry.get_commercial_transformer().build_commercial_information(
            extraction_result,
            traceability=traceability,
        )
        technical_information = self._registry.get_technical_transformer().build_technical_information(
            extraction_result,
            traceability=traceability,
        )
        items = self._registry.get_items_transformer().build_items(
            extraction_result,
            traceability=traceability,
        )
        conditions = self._registry.get_conditions_transformer().build_conditions(
            extraction_result,
            traceability=traceability,
        )
        canonical_observations = self._registry.get_observations_transformer().build_observations(
            extraction_result,
            traceability=traceability,
        )
        metadata = self._registry.get_metadata_transformer().build_metadata(
            extraction_result,
            traceability=traceability,
        )

        representation = CanonicalDocument(
            traceability=traceability,
            provider=provider,
            commercial_information=commercial_information,
            technical_information=technical_information,
            items=items,
            conditions=conditions,
            observations=canonical_observations,
            metadata=metadata,
            immutable=True,
        )

        observations.extend(
            (
                "canonical_representation_immutable=True",
                "traceability_preserved=True",
                f"classification_prepared={classification_integration_prepared}",
            ),
        )

        return CanonicalRepresentationResult(
            process_id=extraction_result.process_id,
            document_id=extraction_result.document_id,
            representation=representation,
            incidents=tuple(incidents),
            original_preserved=traceability.original_preserved,
            classification_integration_prepared=classification_integration_prepared,
            transformers_executed=len(section_results),
            technical_observations=tuple(observations),
        )
