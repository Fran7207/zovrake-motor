"""Extractor de elementos estructurales."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_elements
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult, StructuralElement
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class StructuralElementsExtractor(ContentExtractorPort):
    """Responsabilidad: extraer anexos y elementos estructurales del documento."""

    @property
    def extractor_name(self) -> str:
        return "structural_elements_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Elementos Estructurales"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.STRUCTURAL_ELEMENTS

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        elements_raw = metadata_value(request, "structural_elements", ())
        elements = tuple(
            StructuralElement(
                element_type=str(item.get("element_type", "structural")) if isinstance(item, dict) else "structural",
                content=str(item.get("content", item)) if isinstance(item, dict) else str(item),
                position=index,
            )
            for index, item in enumerate(elements_raw)
        )
        if elements:
            return result_with_elements(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                elements=elements,
                observation="Elementos estructurales obtenidos desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )
