"""Constructor de la entidad Proveedor."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.models import CanonicalDocument
from zovrake_motor.comprehension.internal_model.builders.base import model_reference, prepared_entity_result
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult, InternalProviderEntity, InternalTraceability
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort


class ProviderEntityBuilder(InternalEntityBuilderPort):
    """Responsabilidad: construir la entidad Proveedor."""

    @property
    def builder_name(self) -> str:
        return "provider_entity_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Proveedor"

    @property
    def entity_type(self) -> InternalEntityType:
        return InternalEntityType.PROVIDER

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
            observation="Proveedor construido desde representación canónica",
        )

    def build_entity(
        self,
        representation: CanonicalDocument,
        *,
        traceability: InternalTraceability,
    ) -> InternalProviderEntity:
        provider = representation.provider
        return InternalProviderEntity(
            entity_id=f"provider-{provider.provider_id}",
            provider_id=provider.provider_id,
            name=provider.name,
            document_id=traceability.document_id,
            canonical_reference=provider.source_reference,
            extraction_reference=traceability.extraction_reference_id,
            source_reference=model_reference(traceability, self.entity_type),
            fields=provider.fields,
        )
