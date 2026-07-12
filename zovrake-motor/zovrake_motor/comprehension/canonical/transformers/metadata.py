"""Transformador de la sección Metadatos."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalMetadata,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import MetadataTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class MetadataTransformer(MetadataTransformerPort):
    """Responsabilidad: transformar metadatos de extracción al modelo canónico."""

    @property
    def transformer_name(self) -> str:
        return "metadata_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Metadatos"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.METADATA

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_metadata(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Metadatos transformados desde resultado de extracción",
        )

    def build_metadata(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalMetadata:
        return CanonicalMetadata(
            source_reference=source_reference(traceability.extraction_reference_id, self.section_type),
            extraction_metadata=dict(extraction_result.metadata),
            canonical_fields={
                "adapter_name": extraction_result.adapter_name,
                "extractors_executed": extraction_result.extractors_executed,
                "ocr_integration_prepared": extraction_result.ocr_integration_prepared,
                "schema_version": "1.0",
            },
        )
