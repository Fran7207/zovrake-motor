"""Transformador de la sección Información Comercial."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalCommercialInformation,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import CommercialInformationTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class CommercialInformationTransformer(CommercialInformationTransformerPort):
    """Responsabilidad: transformar información comercial."""

    @property
    def transformer_name(self) -> str:
        return "commercial_information_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Información Comercial"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.COMMERCIAL_INFORMATION

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_commercial_information(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Información comercial transformada desde metadatos de extracción",
        )

    def build_commercial_information(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalCommercialInformation:
        fields = {
            key: value
            for key, value in extraction_result.metadata.items()
            if key.startswith("commercial_")
        }
        return CanonicalCommercialInformation(
            source_reference=source_reference(traceability.extraction_reference_id, self.section_type),
            currency=str(metadata_value(extraction_result, "commercial_currency", "")),
            total_amount=str(metadata_value(extraction_result, "commercial_total_amount", "")),
            payment_terms=str(metadata_value(extraction_result, "commercial_payment_terms", "")),
            fields=fields,
        )
