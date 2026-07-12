"""Constructor de la entidad Referencias al Documento Original."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import (
    EntityBuildResult,
    InternalOriginalReferencesEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class OriginalReferencesEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir referencias al documento original."""

    @property
    def builder_name(self) -> str:
        return "original_references_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Referencias al Documento Original"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.ORIGINAL_REFERENCES

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
    ) -> InternalOriginalReferencesEntity:
        return InternalOriginalReferencesEntity(
            entity_id=f"original-ref-{traceability.document_id}",
            document_id=traceability.document_id,
            document_reference=traceability.document_reference,
            adapter_name=traceability.adapter_name,
            format_type=traceability.format_type,
            canonical_reference_id=traceability.canonical_reference_id,
            extraction_reference_id=traceability.extraction_reference_id,
            original_preserved=traceability.original_preserved,
            source_reference=model_reference(traceability, self.entity_type),
        )
