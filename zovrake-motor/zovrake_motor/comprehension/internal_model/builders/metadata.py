"""Constructor de la entidad Metadatos."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult, InternalMetadataEntity, InternalTraceability
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class MetadataEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir la entidad Metadatos."""

    @property
    def builder_name(self) -> str:
        return "metadata_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Metadatos"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.METADATA

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
    ) -> InternalMetadataEntity:
        metadata = representation.metadata
        return InternalMetadataEntity(
            entity_id=f"metadata-{traceability.document_id}",
            document_id=traceability.document_id,
            canonical_reference=metadata.source_reference,
            extraction_reference=traceability.extraction_reference_id,
            source_reference=model_reference(traceability, self.entity_type),
            canonical_metadata=metadata.canonical_fields,
            extraction_metadata=metadata.extraction_metadata,
            model_fields={"schema_version": representation.schema_version},
        )
