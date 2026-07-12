"""Constructor de la entidad Observaciones."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import (
    EntityBuildResult,
    InternalObservationEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class ObservationsEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir las entidades Observación."""

    @property
    def builder_name(self) -> str:
        return "observations_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Observaciones"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.OBSERVATIONS

    def build(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> EntityBuildResult:
        self.build_entities(representation, traceability=traceability)
        return prepared_entity_result(builder_name=self.builder_name, entity_type=self.entity_type)

    def build_entities(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
    ) -> tuple[InternalObservationEntity, ...]:
        observations: list[InternalObservationEntity] = []
        for observation in representation.observations:
            observations.append(
                InternalObservationEntity(
                    entity_id=f"observation-{observation.observation_id}",
                    observation_id=observation.observation_id,
                    document_id=traceability.document_id,
                    content=observation.content,
                    canonical_reference=observation.source_reference,
                    extraction_reference=traceability.extraction_reference_id,
                    source_reference=f"{model_reference(traceability, self.entity_type)}/{observation.observation_id}",
                    observation_type=observation.observation_type,
                    fields=observation.fields,
                ),
            )
        return tuple(observations)
