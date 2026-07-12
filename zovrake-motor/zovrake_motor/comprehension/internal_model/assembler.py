"""Ensamblador del Modelo Documental Interno."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.models import (
    InternalDocumentModel,
    InternalModelBuildResult,
    InternalTraceability,
    ModelBuildIncident,
)
from zovrake_motor.comprehension.internal_model.registry import EntityBuilderRegistry


class InternalModelAssembler:
    """
    Ensambla el Modelo Documental Interno uniforme a partir de constructores.

    No interpreta el contenido ni modifica la representación canónica.
    """

    def __init__(self, registry: EntityBuilderRegistry) -> None:
        self._registry = registry

    def assemble(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
        classification_integration_prepared: bool,
    ) -> InternalModelBuildResult:
        build_results = []
        incidents: list[ModelBuildIncident] = []
        observations: list[str] = []

        for builder in self._registry.all_builders():
            result = builder.build(
                representation,
                traceability=traceability,
                requirement_code=requirement_code,
                requirement_context=requirement_context,
            )
            build_results.append(result)
            observations.extend(result.technical_observations)
            incidents.extend(result.incidents)

        document = self._registry.get_document_builder().build_entity(representation, traceability=traceability)
        provider = self._registry.get_provider_builder().build_entity(representation, traceability=traceability)
        commercial = self._registry.get_commercial_builder().build_entity(representation, traceability=traceability)
        technical = self._registry.get_technical_builder().build_entity(representation, traceability=traceability)
        items = self._registry.get_items_builder().build_entities(representation, traceability=traceability)
        conditions = self._registry.get_conditions_builder().build_entities(representation, traceability=traceability)
        model_observations = self._registry.get_observations_builder().build_entities(
            representation,
            traceability=traceability,
        )
        metadata = self._registry.get_metadata_builder().build_entity(representation, traceability=traceability)
        requirement = self._registry.get_requirement_context_builder().build_entity(
            representation,
            traceability=traceability,
            requirement_code=requirement_code,
            requirement_context=requirement_context,
        )
        original_refs = self._registry.get_original_references_builder().build_entity(
            representation,
            traceability=traceability,
        )

        model = InternalDocumentModel(
            model_id=traceability.model_id,
            traceability=traceability,
            document=document,
            provider=provider,
            commercial_information=commercial,
            technical_information=technical,
            items=items,
            commercial_conditions=conditions,
            observations=model_observations,
            metadata=metadata,
            requirement_context=requirement,
            original_references=original_refs,
            immutable=True,
            classification_ready=classification_integration_prepared,
        )

        observations.extend(
            (
                "internal_model_immutable=True",
                "traceability_preserved=True",
                f"classification_prepared={classification_integration_prepared}",
            ),
        )

        return InternalModelBuildResult(
            process_id=traceability.process_id,
            document_id=traceability.document_id,
            model=model,
            incidents=tuple(incidents),
            original_preserved=traceability.original_preserved,
            classification_integration_prepared=classification_integration_prepared,
            builders_executed=len(build_results),
            technical_observations=tuple(observations),
        )
