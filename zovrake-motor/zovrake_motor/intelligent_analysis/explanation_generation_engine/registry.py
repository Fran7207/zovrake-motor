"""Registro centralizado de generadores del EGE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.explanation_generation_engine.exceptions import (
    ExplanationGeneratorNotFoundError,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.generators_strategies import (
    OrganizedAnalysisExplanationGenerator,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.port import (
    ExplanationGeneratorPort,
)
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings


class ExplanationGeneratorRegistry:
    """
    Registro único de generadores de explicaciones.

    Todo generador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._generators_by_name: dict[str, ExplanationGeneratorPort] = {}
        self._generators_ordered: list[ExplanationGeneratorPort] = []

    def register(self, generator: ExplanationGeneratorPort) -> None:
        if generator.generator_name in self._generators_by_name:
            raise ValueError(f"Generador ya registrado: {generator.generator_name}")
        self._generators_by_name[generator.generator_name] = generator
        self._generators_ordered.append(generator)

    def register_defaults(
        self,
        *,
        settings: ExplanationGenerationEngineSettings | None = None,
    ) -> None:
        settings = settings or ExplanationGenerationEngineSettings.default()
        candidates: list[tuple[bool, ExplanationGeneratorPort]] = [
            (
                settings.organized_explanation_generator_enabled,
                OrganizedAnalysisExplanationGenerator(),
            ),
        ]
        for enabled, generator in candidates:
            if enabled:
                self.register(generator)

    def get(self, name: str) -> ExplanationGeneratorPort | None:
        return self._generators_by_name.get(name)

    def require(self, name: str) -> ExplanationGeneratorPort:
        generator = self.get(name)
        if generator is None:
            raise ExplanationGeneratorNotFoundError(f"Generador no registrado: {name}")
        return generator

    def all_generators(self) -> tuple[ExplanationGeneratorPort, ...]:
        return tuple(self._generators_ordered)

    def count(self) -> int:
        return len(self._generators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [generator.snapshot() for generator in self._generators_ordered]
