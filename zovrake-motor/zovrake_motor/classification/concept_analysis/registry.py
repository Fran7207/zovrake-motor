"""Registro centralizado de detectores del CAE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_analysis.detectors import (
    CommercialConceptDetector,
    CommercialConditionDetector,
    ItemConceptDetector,
    ObservationConceptDetector,
    TechnicalConceptDetector,
)
from zovrake_motor.classification.concept_analysis.exceptions import ConceptDetectorNotFoundError
from zovrake_motor.classification.concept_analysis.port import ConceptDetectorPort
from zovrake_motor.config.categories.classification import ConceptAnalysisSettings


class ConceptDetectorRegistry:
    """
    Registro único de detectores de conceptos.

    Todo detector debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._detectors_by_name: dict[str, ConceptDetectorPort] = {}
        self._detectors_ordered: list[ConceptDetectorPort] = []

    def register(self, detector: ConceptDetectorPort) -> None:
        if detector.detector_name in self._detectors_by_name:
            raise ValueError(f"Detector ya registrado: {detector.detector_name}")
        self._detectors_by_name[detector.detector_name] = detector
        self._detectors_ordered.append(detector)

    def register_defaults(self, *, settings: ConceptAnalysisSettings | None = None) -> None:
        settings = settings or ConceptAnalysisSettings.default()
        candidates: list[tuple[bool, ConceptDetectorPort]] = [
            (settings.item_detector_enabled, ItemConceptDetector()),
            (settings.technical_detector_enabled, TechnicalConceptDetector()),
            (settings.commercial_detector_enabled, CommercialConceptDetector()),
            (settings.condition_detector_enabled, CommercialConditionDetector()),
            (settings.observation_detector_enabled, ObservationConceptDetector()),
        ]
        for enabled, detector in candidates:
            if enabled:
                self.register(detector)

    def get(self, name: str) -> ConceptDetectorPort | None:
        return self._detectors_by_name.get(name)

    def require(self, name: str) -> ConceptDetectorPort:
        detector = self.get(name)
        if detector is None:
            raise ConceptDetectorNotFoundError(f"Detector no registrado: {name}")
        return detector

    def all_detectors(self) -> tuple[ConceptDetectorPort, ...]:
        return tuple(self._detectors_ordered)

    def count(self) -> int:
        return len(self._detectors_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [detector.snapshot() for detector in self._detectors_ordered]
