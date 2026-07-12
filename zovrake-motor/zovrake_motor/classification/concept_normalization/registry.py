"""Registro centralizado de normalizadores del CNE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_normalization.exceptions import ConceptNormalizerNotFoundError
from zovrake_motor.classification.concept_normalization.normalizers import (
    CommercialElementNormalizer,
    MaterialConceptNormalizer,
    PartidaConceptNormalizer,
    ServiceConceptNormalizer,
    SpecificationNormalizer,
    TechnicalElementNormalizer,
)
from zovrake_motor.classification.concept_normalization.port import ConceptNormalizerPort
from zovrake_motor.config.categories.classification import ConceptNormalizationSettings


class ConceptNormalizerRegistry:
    """
    Registro único de normalizadores de conceptos.

    Todo normalizador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._normalizers_by_name: dict[str, ConceptNormalizerPort] = {}
        self._normalizers_ordered: list[ConceptNormalizerPort] = []

    def register(self, normalizer: ConceptNormalizerPort) -> None:
        if normalizer.normalizer_name in self._normalizers_by_name:
            raise ValueError(f"Normalizador ya registrado: {normalizer.normalizer_name}")
        self._normalizers_by_name[normalizer.normalizer_name] = normalizer
        self._normalizers_ordered.append(normalizer)

    def register_defaults(self, *, settings: ConceptNormalizationSettings | None = None) -> None:
        settings = settings or ConceptNormalizationSettings.default()
        candidates: list[tuple[bool, ConceptNormalizerPort]] = [
            (settings.material_normalizer_enabled, MaterialConceptNormalizer()),
            (settings.partida_normalizer_enabled, PartidaConceptNormalizer()),
            (settings.service_normalizer_enabled, ServiceConceptNormalizer()),
            (settings.technical_element_normalizer_enabled, TechnicalElementNormalizer()),
            (settings.commercial_element_normalizer_enabled, CommercialElementNormalizer()),
            (settings.specification_normalizer_enabled, SpecificationNormalizer()),
        ]
        for enabled, normalizer in candidates:
            if enabled:
                self.register(normalizer)

    def get(self, name: str) -> ConceptNormalizerPort | None:
        return self._normalizers_by_name.get(name)

    def require(self, name: str) -> ConceptNormalizerPort:
        normalizer = self.get(name)
        if normalizer is None:
            raise ConceptNormalizerNotFoundError(f"Normalizador no registrado: {name}")
        return normalizer

    def all_normalizers(self) -> tuple[ConceptNormalizerPort, ...]:
        return tuple(self._normalizers_ordered)

    def count(self) -> int:
        return len(self._normalizers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [normalizer.snapshot() for normalizer in self._normalizers_ordered]
