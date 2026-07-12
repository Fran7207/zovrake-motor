"""Extractor de pies de página."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_elements
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult, StructuralElement
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class FootersExtractor(ContentExtractorPort):
    """Responsabilidad: extraer pies de página del documento."""

    @property
    def extractor_name(self) -> str:
        return "footers_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Pies de Página"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.FOOTERS

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        footers = metadata_value(request, "footers", ())
        elements = tuple(
            StructuralElement(element_type="footer", content=str(item), position=index)
            for index, item in enumerate(footers)
        )
        if elements:
            return result_with_elements(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                elements=elements,
                observation="Pies de página obtenidos desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )
