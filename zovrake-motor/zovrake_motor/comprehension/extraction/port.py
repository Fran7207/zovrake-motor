"""Contrato base de extractores del Content Extraction Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractorResult


class ContentExtractorPort(ABC):
    """
    Contrato común para todos los extractores especializados.

    Cada extractor tiene una única responsabilidad y preserva el documento original.
    """

    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """Identificador único del extractor."""

    @property
    @abstractmethod
    def extractor_label(self) -> str:
        """Etiqueta descriptiva del extractor."""

    @property
    @abstractmethod
    def extractor_type(self) -> ExtractorType:
        """Tipo de contenido que extrae."""

    @abstractmethod
    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        """Extrae contenido estructural — sin interpretación en esta etapa."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "extractor_name": self.extractor_name,
            "extractor_label": self.extractor_label,
            "extractor_type": self.extractor_type.value,
        }
