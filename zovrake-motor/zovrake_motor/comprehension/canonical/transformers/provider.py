"""Transformador de la sección Proveedor."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalProvider,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import ProviderTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class ProviderTransformer(ProviderTransformerPort):
    """Responsabilidad: transformar información del proveedor."""

    @property
    def transformer_name(self) -> str:
        return "provider_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Proveedor"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.PROVIDER

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_provider(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Proveedor transformado desde metadatos de extracción",
        )

    def build_provider(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalProvider:
        name = str(metadata_value(extraction_result, "provider_name", ""))
        provider_id = str(metadata_value(extraction_result, "provider_id", traceability.document_id))
        fields = {
            key: value
            for key, value in extraction_result.metadata.items()
            if key.startswith("provider_")
        }
        return CanonicalProvider(
            provider_id=provider_id,
            name=name,
            source_reference=source_reference(traceability.extraction_reference_id, self.section_type),
            fields=fields,
        )
