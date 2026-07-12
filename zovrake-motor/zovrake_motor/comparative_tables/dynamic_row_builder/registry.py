"""Registro centralizado de constructores del DRB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_row_builder.builders_strategies import ProviderRowBuilder
from zovrake_motor.comparative_tables.dynamic_row_builder.exceptions import RowBuilderNotFoundError
from zovrake_motor.comparative_tables.dynamic_row_builder.port import DynamicRowBuilderPort
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings


class RowBuilderRegistry:
    """
    Registro único de constructores de filas dinámicas.

    Todo constructor debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._builders_by_name: dict[str, DynamicRowBuilderPort] = {}
        self._builders_ordered: list[DynamicRowBuilderPort] = []

    def register(self, builder: DynamicRowBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(self, *, settings: DynamicRowBuilderSettings | None = None) -> None:
        settings = settings or DynamicRowBuilderSettings.default()
        candidates: list[tuple[bool, DynamicRowBuilderPort]] = [
            (settings.provider_row_builder_enabled, ProviderRowBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> DynamicRowBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> DynamicRowBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise RowBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[DynamicRowBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
