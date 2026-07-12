"""Registro centralizado de constructores del CGB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.comparable_group_builder.builders_strategies import (
    EquivalenceClusterGroupBuilder,
)
from zovrake_motor.classification.comparable_group_builder.exceptions import GroupBuilderNotFoundError
from zovrake_motor.classification.comparable_group_builder.port import ComparableGroupBuilderPort
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings


class GroupBuilderRegistry:
    """
    Registro único de constructores de grupos comparables.

    Todo constructor debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._builders_by_name: dict[str, ComparableGroupBuilderPort] = {}
        self._builders_ordered: list[ComparableGroupBuilderPort] = []

    def register(self, builder: ComparableGroupBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(self, *, settings: ComparableGroupBuilderSettings | None = None) -> None:
        settings = settings or ComparableGroupBuilderSettings.default()
        candidates: list[tuple[bool, ComparableGroupBuilderPort]] = [
            (settings.equivalence_cluster_builder_enabled, EquivalenceClusterGroupBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> ComparableGroupBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> ComparableGroupBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise GroupBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[ComparableGroupBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
