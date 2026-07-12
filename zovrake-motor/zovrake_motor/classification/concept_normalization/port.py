"""Contrato base de normalizadores del Concept Normalization Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.concept_normalization.enums import ConceptNormalizerType
from zovrake_motor.classification.concept_normalization.gateway import ClassificationCatalogView
from zovrake_motor.classification.concept_normalization.models import NormalizerResult


class ConceptNormalizerPort(ABC):
    """
    Contrato común para normalizadores de conceptos.

    Cada normalizador produce representación uniforme sin modificar el valor original.
    """

    @property
    @abstractmethod
    def normalizer_name(self) -> str:
        """Identificador único del normalizador."""

    @property
    @abstractmethod
    def normalizer_label(self) -> str:
        """Etiqueta descriptiva del normalizador."""

    @property
    @abstractmethod
    def normalizer_type(self) -> ConceptNormalizerType:
        """Tipo de conceptos que normaliza."""

    @abstractmethod
    def normalize(self, catalog_view: ClassificationCatalogView, *, start_sequence: int) -> NormalizerResult:
        """Normaliza conceptos — sin modificar catálogos de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "normalizer_name": self.normalizer_name,
            "normalizer_label": self.normalizer_label,
            "normalizer_type": self.normalizer_type.value,
        }
