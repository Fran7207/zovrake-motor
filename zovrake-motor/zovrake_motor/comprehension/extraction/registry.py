"""Registro centralizado de extractores del CEE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.extraction.exceptions import ExtractorNotFoundError
from zovrake_motor.comprehension.extraction.extractors import (
    EmbeddedImagesExtractor,
    FootersExtractor,
    HeadersExtractor,
    ListsExtractor,
    MetadataExtractor,
    StructuralElementsExtractor,
    TablesExtractor,
    TextExtractor,
)
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort
from zovrake_motor.config.categories.comprehension import DocumentExtractionSettings


class ExtractorRegistry:
    """
    Registro único de extractores especializados.

    Todo extractor debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._extractors_by_name: dict[str, ContentExtractorPort] = {}
        self._extractors_ordered: list[ContentExtractorPort] = []

    def register(self, extractor: ContentExtractorPort) -> None:
        if extractor.extractor_name in self._extractors_by_name:
            raise ValueError(f"Extractor ya registrado: {extractor.extractor_name}")
        self._extractors_by_name[extractor.extractor_name] = extractor
        self._extractors_ordered.append(extractor)

    def register_defaults(self, *, settings: DocumentExtractionSettings | None = None) -> None:
        settings = settings or DocumentExtractionSettings.default()
        candidates: list[tuple[bool, ContentExtractorPort]] = [
            (settings.text_extractor_enabled, TextExtractor()),
            (settings.tables_extractor_enabled, TablesExtractor()),
            (settings.metadata_extractor_enabled, MetadataExtractor()),
            (settings.headers_extractor_enabled, HeadersExtractor()),
            (settings.footers_extractor_enabled, FootersExtractor()),
            (settings.lists_extractor_enabled, ListsExtractor()),
            (settings.embedded_images_extractor_enabled, EmbeddedImagesExtractor()),
            (settings.structural_elements_extractor_enabled, StructuralElementsExtractor()),
        ]
        for enabled, extractor in candidates:
            if enabled:
                self.register(extractor)

    def get(self, name: str) -> ContentExtractorPort | None:
        return self._extractors_by_name.get(name)

    def require(self, name: str) -> ContentExtractorPort:
        extractor = self.get(name)
        if extractor is None:
            raise ExtractorNotFoundError(f"Extractor no registrado: {name}")
        return extractor

    def all_extractors(self) -> tuple[ContentExtractorPort, ...]:
        return tuple(self._extractors_ordered)

    def count(self) -> int:
        return len(self._extractors_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [extractor.snapshot() for extractor in self._extractors_ordered]
