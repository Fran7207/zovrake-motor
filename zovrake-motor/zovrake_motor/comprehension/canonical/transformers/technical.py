"""Transformador de la sección Información Técnica."""

from __future__ import annotations

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalTechnicalInformation,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import TechnicalInformationTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class TechnicalInformationTransformer(TechnicalInformationTransformerPort):
    """Responsabilidad: transformar información técnica."""

    @property
    def transformer_name(self) -> str:
        return "technical_information_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Información Técnica"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.TECHNICAL_INFORMATION

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_technical_information(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Información técnica transformada desde elementos estructurales",
        )

    def build_technical_information(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalTechnicalInformation:
        specifications = tuple(
            element.content
            for element in extraction_result.structural_elements
            if element.element_type in {"technical", "specification", "technical_information"}
        )
        fields = {
            key: value
            for key, value in extraction_result.metadata.items()
            if key.startswith("technical_")
        }
        return CanonicalTechnicalInformation(
            source_reference=source_reference(traceability.extraction_reference_id, self.section_type),
            specifications=specifications,
            fields=fields if fields else {"raw_text": metadata_value(extraction_result, "technical_text", "")},
        )
