"""Constructor de la entidad Documento."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult, InternalDocumentEntity, InternalTraceability
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class DocumentEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir la entidad Documento."""

    @property
    def builder_name(self) -> str:
        return "document_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Documento"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.DOCUMENT

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
            observation="Documento construido desde representación canónica",
        )

    def build_entity(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
    ) -> InternalDocumentEntity:
        return InternalDocumentEntity(
            entity_id=f"doc-{traceability.document_id}",
            document_id=traceability.document_id,
            model_id=traceability.model_id,
            canonical_reference=traceability.canonical_reference_id,
            source_reference=model_reference(traceability, self.entity_type),
            schema_version=representation.schema_version,
        )
