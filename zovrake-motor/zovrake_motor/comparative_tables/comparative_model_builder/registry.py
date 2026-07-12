"""Registro centralizado de constructores del CMB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_model_builder.builders_strategies import (
    GroupComparativeModelBuilder,
)
from zovrake_motor.comparative_tables.comparative_model_builder.exceptions import (
    ModelBuilderNotFoundError,
)
from zovrake_motor.comparative_tables.comparative_model_builder.port import ModelBuilderPort
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings


class ModelBuilderRegistry:
    """Registro único de constructores del Modelo Comparativo Definitivo."""

    def __init__(self) -> None:
        self._builders_by_name: dict[str, ModelBuilderPort] = {}
        self._builders_ordered: list[ModelBuilderPort] = []

    def register(self, builder: ModelBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(
        self,
        *,
        settings: ComparativeModelBuilderSettings | None = None,
    ) -> None:
        settings = settings or ComparativeModelBuilderSettings.default()
        candidates: list[tuple[bool, ModelBuilderPort]] = [
            (settings.group_comparative_model_builder_enabled, GroupComparativeModelBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> ModelBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> ModelBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise ModelBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[ModelBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
