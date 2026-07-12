"""Extractores especializados del Content Extraction Engine."""

from zovrake_motor.comprehension.extraction.extractors.embedded_images import EmbeddedImagesExtractor
from zovrake_motor.comprehension.extraction.extractors.footers import FootersExtractor
from zovrake_motor.comprehension.extraction.extractors.headers import HeadersExtractor
from zovrake_motor.comprehension.extraction.extractors.lists import ListsExtractor
from zovrake_motor.comprehension.extraction.extractors.metadata import MetadataExtractor
from zovrake_motor.comprehension.extraction.extractors.structural_elements import StructuralElementsExtractor
from zovrake_motor.comprehension.extraction.extractors.tables import TablesExtractor
from zovrake_motor.comprehension.extraction.extractors.text import TextExtractor

__all__ = [
    "EmbeddedImagesExtractor",
    "FootersExtractor",
    "HeadersExtractor",
    "ListsExtractor",
    "MetadataExtractor",
    "StructuralElementsExtractor",
    "TablesExtractor",
    "TextExtractor",
]
