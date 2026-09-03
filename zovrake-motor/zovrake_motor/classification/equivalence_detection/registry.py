"""Registro centralizado de detectores del EDE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.equivalence_detection.detectors import (
    CrossTypeDistinctDetector,
    ExactNormalizedMatchDetector,
    SharedOriginRelationDetector,
)
from zovrake_motor.classification.equivalence_detection.exceptions import EquivalenceDetectorNotFoundError
from zovrake_motor.classification.equivalence_detection.semantic_detector import SemanticSimilarityRelationDetector
from zovrake_motor.classification.equivalence_detection.port import EquivalenceDetectorPort
from zovrake_motor.config.categories.classification import EquivalenceDetectionSettings


class EquivalenceDetectorRegistry:
    """
    Registro único de detectores de equivalencias.

    Todo detector debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._detectors_by_name: dict[str, EquivalenceDetectorPort] = {}
        self._detectors_ordered: list[EquivalenceDetectorPort] = []

    def register(self, detector: EquivalenceDetectorPort) -> None:
        if detector.detector_name in self._detectors_by_name:
            raise ValueError(f"Detector ya registrado: {detector.detector_name}")
        self._detectors_by_name[detector.detector_name] = detector
        self._detectors_ordered.append(detector)

    def register_defaults(self, *, settings: EquivalenceDetectionSettings | None = None) -> None:
        settings = settings or EquivalenceDetectionSettings.default()
        candidates: list[tuple[bool, EquivalenceDetectorPort]] = [
            (settings.exact_match_detector_enabled, ExactNormalizedMatchDetector()),
            (settings.cross_type_distinct_detector_enabled, CrossTypeDistinctDetector()),
            (settings.shared_origin_relation_detector_enabled, SharedOriginRelationDetector()),
            (
                settings.semantic_similarity_enabled,
                SemanticSimilarityRelationDetector(),
            ),
        ]
        for enabled, detector in candidates:
            if enabled:
                self.register(detector)

    def get(self, name: str) -> EquivalenceDetectorPort | None:
        return self._detectors_by_name.get(name)

    def require(self, name: str) -> EquivalenceDetectorPort:
        detector = self.get(name)
        if detector is None:
            raise EquivalenceDetectorNotFoundError(f"Detector no registrado: {name}")
        return detector

    def all_detectors(self) -> tuple[EquivalenceDetectorPort, ...]:
        return tuple(self._detectors_ordered)

    def count(self) -> int:
        return len(self._detectors_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [detector.snapshot() for detector in self._detectors_ordered]
