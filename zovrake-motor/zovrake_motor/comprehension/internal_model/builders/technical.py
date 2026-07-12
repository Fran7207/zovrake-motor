"""Constructor de la entidad Información Técnica."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import (
    EntityBuildResult,
    InternalTechnicalInformationEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class TechnicalInformationEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir la entidad Información Técnica."""

    @property
    def builder_name(self) -> str:
        return "technical_information_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Información Técnica"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.TECHNICAL_INFORMATION

    def build(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> EntityBuildResult:
        self.build_entity(representation, traceability=traceability)
        return prepared_entity_result(builder_name=self.builder_name, entity_type=self.entity_type)

    def build_entity(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
    ) -> InternalTechnicalInformationEntity:
        technical = representation.technical_information
        return InternalTechnicalInformationEntity(
            entity_id=f"technical-{traceability.document_id}",
            document_id=traceability.document_id,
            canonical_reference=technical.source_reference,
            extraction_reference=traceability.extraction_reference_id,
            source_reference=model_reference(traceability, self.entity_type),
            specifications=technical.specifications,
            fields=technical.fields,
        )
