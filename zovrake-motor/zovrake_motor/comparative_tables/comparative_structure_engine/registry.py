"""Registro centralizado de constructores del CSE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_structure_engine.builders_strategies import (
    DomainModelGroupStructureBuilder,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.exceptions import (
    StructureBuilderNotFoundError,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.port import (
    ComparativeStructureBuilderPort,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings


class StructureBuilderRegistry:
    """
    Registro único de constructores de estructuras comparativas.

    Todo constructor debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._builders_by_name: dict[str, ComparativeStructureBuilderPort] = {}
        self._builders_ordered: list[ComparativeStructureBuilderPort] = []

    def register(self, builder: ComparativeStructureBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(self, *, settings: ComparativeStructureEngineSettings | None = None) -> None:
        settings = settings or ComparativeStructureEngineSettings.default()
        candidates: list[tuple[bool, ComparativeStructureBuilderPort]] = [
            (settings.domain_model_group_structure_builder_enabled, DomainModelGroupStructureBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> ComparativeStructureBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> ComparativeStructureBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise StructureBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[ComparativeStructureBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
