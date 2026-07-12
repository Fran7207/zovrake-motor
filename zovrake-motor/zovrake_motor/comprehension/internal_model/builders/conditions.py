"""Constructor de la entidad Condiciones Comerciales."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import (
    EntityBuildResult,
    InternalCommercialConditionEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class CommercialConditionsEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir las entidades Condición Comercial."""

    @property
    def builder_name(self) -> str:
        return "commercial_conditions_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Condiciones Comerciales"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.COMMERCIAL_CONDITIONS

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
    ) -> tuple[InternalCommercialConditionEntity, ...]:
        conditions: list[InternalCommercialConditionEntity] = []
        for condition in representation.conditions:
            conditions.append(
                InternalCommercialConditionEntity(
                    entity_id=f"condition-{condition.condition_id}",
                    condition_id=condition.condition_id,
                    document_id=traceability.document_id,
                    content=condition.content,
                    canonical_reference=condition.source_reference,
                    extraction_reference=traceability.extraction_reference_id,
                    source_reference=f"{model_reference(traceability, self.entity_type)}/{condition.condition_id}",
                    condition_type=condition.condition_type,
                    fields=condition.fields,
                ),
            )
        return tuple(conditions)
