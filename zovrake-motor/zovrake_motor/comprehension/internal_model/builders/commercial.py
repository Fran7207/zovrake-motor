"""Constructor de la entidad Información Comercial."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import (
    EntityBuildResult,
    InternalCommercialInformationEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class CommercialInformationEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir la entidad Información Comercial."""

    @property
    def builder_name(self) -> str:
        return "commercial_information_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Información Comercial"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.COMMERCIAL_INFORMATION

    def build(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
        requirement_code: str = "",
        requirement_context: dict[str, Any] | None = None,
    ) -> EntityBuildResult:
        self.build_entity(representation, traceability=traceability)
        return prepared_entity_result(
            builder_name=self.builder_name,
            entity_type=self.entity_type,
        )

    def build_entity(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
    ) -> InternalCommercialInformationEntity:
        commercial = representation.commercial_information
        return InternalCommercialInformationEntity(
            entity_id=f"commercial-{traceability.document_id}",
            document_id=traceability.document_id,
            canonical_reference=commercial.source_reference,
            extraction_reference=traceability.extraction_reference_id,
            source_reference=model_reference(traceability, self.entity_type),
            currency=commercial.currency,
            total_amount=commercial.total_amount,
            payment_terms=commercial.payment_terms,
            fields=commercial.fields,
        )
