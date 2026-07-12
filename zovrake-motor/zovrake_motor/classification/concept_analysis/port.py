"""Contrato base de detectores del Concept Analysis Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.classification.concept_analysis.enums import ConceptDetectorType
from zovrake_motor.classification.concept_analysis.gateway import InternalModelView
from zovrake_motor.classification.concept_analysis.models import DetectorResult


class ConceptDetectorPort(ABC):
    """
    Contrato común para detectores de conceptos.

    Cada detector identifica conceptos de una sección del modelo interno.
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
    def detector_type(self) -> ConceptDetectorType:
        """Tipo de conceptos que detecta."""

    @abstractmethod
    def detect(self, model_view: InternalModelView, *, start_sequence: int) -> DetectorResult:
        """Identifica conceptos candidatos — sin clasificación."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "detector_name": self.detector_name,
            "detector_label": self.detector_label,
            "detector_type": self.detector_type.value,
        }
