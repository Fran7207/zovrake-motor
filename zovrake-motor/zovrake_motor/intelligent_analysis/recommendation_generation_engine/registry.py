"""Registro centralizado de generadores del RGE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.exceptions import (
    RecommendationGeneratorNotFoundError,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.generators_strategies import (
    OrganizedEvidenceRecommendationGenerator,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.port import (
    RecommendationGeneratorPort,
)
from zovrake_motor.config.categories.intelligent_analysis import RecommendationGenerationEngineSettings


class RecommendationGeneratorRegistry:
    """Registro único de generadores de recomendaciones."""

    def __init__(self) -> None:
        self._generators_by_name: dict[str, RecommendationGeneratorPort] = {}
        self._generators_ordered: list[RecommendationGeneratorPort] = []

    def register(self, generator: RecommendationGeneratorPort) -> None:
        if generator.generator_name in self._generators_by_name:
            raise ValueError(f"Generador ya registrado: {generator.generator_name}")
        self._generators_by_name[generator.generator_name] = generator
        self._generators_ordered.append(generator)

    def register_defaults(
        self,
        *,
        settings: RecommendationGenerationEngineSettings | None = None,
    ) -> None:
        settings = settings or RecommendationGenerationEngineSettings.default()
        candidates: list[tuple[bool, RecommendationGeneratorPort]] = [
            (
                settings.organized_recommendation_generator_enabled,
                OrganizedEvidenceRecommendationGenerator(),
            ),
        ]
        for enabled, generator in candidates:
            if enabled:
                self.register(generator)

    def get(self, name: str) -> RecommendationGeneratorPort | None:
        return self._generators_by_name.get(name)

    def require(self, name: str) -> RecommendationGeneratorPort:
        generator = self.get(name)
        if generator is None:
            raise RecommendationGeneratorNotFoundError(f"Generador no registrado: {name}")
        return generator

    def all_generators(self) -> tuple[RecommendationGeneratorPort, ...]:
        return tuple(self._generators_ordered)

    def count(self) -> int:
        return len(self._generators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [generator.snapshot() for generator in self._generators_ordered]
