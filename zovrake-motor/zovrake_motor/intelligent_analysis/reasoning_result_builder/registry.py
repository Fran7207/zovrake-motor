"""Registro centralizado de constructores del RRB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.reasoning_result_builder.builders_strategies import (
    OrganizedReasoningResultBuilder,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.exceptions import (
    ReasoningResultBuilderNotFoundError,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.port import ReasoningResultBuilderPort
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings


class ReasoningResultBuilderRegistry:
    """Registro único de constructores de resultados."""

    def __init__(self) -> None:
        self._builders_by_name: dict[str, ReasoningResultBuilderPort] = {}
        self._builders_ordered: list[ReasoningResultBuilderPort] = []

    def register(self, builder: ReasoningResultBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(
        self,
        *,
        settings: ReasoningResultBuilderSettings | None = None,
    ) -> None:
        settings = settings or ReasoningResultBuilderSettings.default()
        candidates: list[tuple[bool, ReasoningResultBuilderPort]] = [
            (settings.organized_result_builder_enabled, OrganizedReasoningResultBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> ReasoningResultBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> ReasoningResultBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise ReasoningResultBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[ReasoningResultBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
