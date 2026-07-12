"""Contrato base de detectores del Equivalence Detection Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.equivalence_detection.enums import EquivalenceDetectorType
from zovrake_motor.classification.equivalence_detection.gateway import NormalizedConceptCatalogView
from zovrake_motor.classification.equivalence_detection.models import DetectorResult


class EquivalenceDetectorPort(ABC):
    """
    Contrato común para detectores de equivalencias.

    Cada detector identifica relaciones sin modificar el catálogo normalizado.
    """

    @property
    @abstractmethod
    def detector_name(self) -> str:
        """Identificador único del detector."""

    @property
    @abstractmethod
    def detector_label(self) -> str:
        """Etiqueta descriptiva del detector."""

    @property
    @abstractmethod
    def detector_type(self) -> EquivalenceDetectorType:
        """Tipo de relaciones que detecta."""

    @abstractmethod
    def detect(self, catalog_view: NormalizedConceptCatalogView, *, start_sequence: int) -> DetectorResult:
        """Detecta relaciones — sin modificar el catálogo normalizado."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "detector_name": self.detector_name,
            "detector_label": self.detector_label,
            "detector_type": self.detector_type.value,
        }
