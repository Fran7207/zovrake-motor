"""Registro centralizado de constructores del DCB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_column_builder.builders_strategies import (
    StructureAttributeColumnBuilder,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.exceptions import (
    ColumnBuilderNotFoundError,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.port import DynamicColumnBuilderPort
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


class ColumnBuilderRegistry:
    """
    Registro único de constructores de columnas dinámicas.

    Todo constructor debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._builders_by_name: dict[str, DynamicColumnBuilderPort] = {}
        self._builders_ordered: list[DynamicColumnBuilderPort] = []

    def register(self, builder: DynamicColumnBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(self, *, settings: DynamicColumnBuilderSettings | None = None) -> None:
        settings = settings or DynamicColumnBuilderSettings.default()
        candidates: list[tuple[bool, DynamicColumnBuilderPort]] = [
            (settings.structure_attribute_column_builder_enabled, StructureAttributeColumnBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> DynamicColumnBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> DynamicColumnBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise ColumnBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[DynamicColumnBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
