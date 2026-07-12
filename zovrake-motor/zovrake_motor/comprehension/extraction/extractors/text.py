"""Extractor de texto."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_text
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class TextExtractor(ContentExtractorPort):
    """Responsabilidad: extraer contenido textual del documento."""

    @property
    def extractor_name(self) -> str:
        return "text_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Texto"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.TEXT

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        text = metadata_value(request, "text_content", "")
        if text:
            return result_with_text(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                text=str(text),
                observation="Texto obtenido desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )
