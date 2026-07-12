"""Extractor de metadatos."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_metadata
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class MetadataExtractor(ContentExtractorPort):
    """Responsabilidad: extraer metadatos del documento."""

    @property
    def extractor_name(self) -> str:
        return "metadata_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Metadatos"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.METADATA

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        document_metadata = metadata_value(request, "document_metadata", {})
        if document_metadata:
            return result_with_metadata(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                metadata=dict(document_metadata),
                observation="Metadatos obtenidos desde el adaptador documental",
            )

        base_metadata = {
            "adapter_name": request.adapter_context.adapter_name,
            "format_type": request.adapter_context.format_type,
            "document_reference": request.adapter_context.document_reference,
        }
        return result_with_metadata(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
            metadata=base_metadata,
            observation="Metadatos estructurales del adaptador documental",
        )
