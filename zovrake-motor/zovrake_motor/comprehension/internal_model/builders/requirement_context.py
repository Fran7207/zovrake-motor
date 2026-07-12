"""Constructor de la entidad Contexto del Requerimiento."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result, requirement_fields
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import (
    EntityBuildResult,
    InternalRequirementContextEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class RequirementContextEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir la entidad Contexto del Requerimiento."""

    @property
    def builder_name(self) -> str:
        return "requirement_context_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Contexto del Requerimiento"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.REQUIREMENT_CONTEXT

    def build(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> EntityBuildResult:
        self.build_entity(
            representation,
            traceability=traceability,
            requirement_code=requirement_code,
            requirement_context=requirement_context,
        )
        return prepared_entity_result(builder_name=self.builder_name, entity_type=self.entity_type)

    def build_entity(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> InternalRequirementContextEntity:
        return InternalRequirementContextEntity(
            entity_id=f"requirement-{traceability.document_id}",
            document_id=traceability.document_id,
            requirement_code=requirement_code,
            process_id=traceability.process_id,
            canonical_reference=traceability.canonical_reference_id,
            extraction_reference=traceability.extraction_reference_id,
            source_reference=model_reference(traceability, self.entity_type),
            fields=requirement_fields(requirement_context),
        )
