"""Extractor de listas."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_elements
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult, StructuralElement
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class ListsExtractor(ContentExtractorPort):
    """Responsabilidad: extraer listas del documento."""

    @property
    def extractor_name(self) -> str:
        return "lists_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Listas"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.LISTS

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        lists = metadata_value(request, "lists", ())
        elements = tuple(
            StructuralElement(element_type="list_item", content=str(item), position=index)
            for index, item in enumerate(lists)
        )
        if elements:
            return result_with_elements(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                elements=elements,
                observation="Listas obtenidas desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )
