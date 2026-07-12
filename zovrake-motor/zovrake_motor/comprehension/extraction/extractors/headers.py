"""Extractor de encabezados."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_elements
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult, StructuralElement
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class HeadersExtractor(ContentExtractorPort):
    """Responsabilidad: extraer encabezados del documento."""

    @property
    def extractor_name(self) -> str:
        return "headers_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Encabezados"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.HEADERS

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        headers = metadata_value(request, "headers", ())
        elements = tuple(
            StructuralElement(element_type="header", content=str(item), position=index)
            for index, item in enumerate(headers)
        )
        if elements:
            return result_with_elements(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                elements=elements,
                observation="Encabezados obtenidos desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )
