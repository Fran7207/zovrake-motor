"""Extractor de imágenes embebidas."""

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_elements
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult, StructuralElement
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class EmbeddedImagesExtractor(ContentExtractorPort):
    """Responsabilidad: detectar imágenes embebidas en el documento."""

    @property
    def extractor_name(self) -> str:
        return "embedded_images_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Imágenes Embebidas"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.EMBEDDED_IMAGES

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        images = metadata_value(request, "embedded_images", ())
        elements = tuple(
            StructuralElement(element_type="embedded_image", content=str(item), position=index)
            for index, item in enumerate(images)
        )
        if elements:
            return result_with_elements(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                elements=elements,
                observation="Imágenes embebidas obtenidas desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )
