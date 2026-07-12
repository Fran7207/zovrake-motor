"""Registro centralizado de constructores del CDMB."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.comparative_domain_model.builders_strategies import (
    GroupContextAggregationBuilder,
)
from zovrake_motor.classification.comparative_domain_model.exceptions import DomainModelBuilderNotFoundError
from zovrake_motor.classification.comparative_domain_model.port import ComparativeDomainModelBuilderPort
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings


class DomainModelBuilderRegistry:
    """Registro único de constructores del modelo comparativo."""

    def __init__(self) -> None:
        self._builders_by_name: dict[str, ComparativeDomainModelBuilderPort] = {}
        self._builders_ordered: list[ComparativeDomainModelBuilderPort] = []

    def register(self, builder: ComparativeDomainModelBuilderPort) -> None:
        if builder.builder_name in self._builders_by_name:
            raise ValueError(f"Constructor ya registrado: {builder.builder_name}")
        self._builders_by_name[builder.builder_name] = builder
        self._builders_ordered.append(builder)

    def register_defaults(self, *, settings: ComparativeDomainModelBuilderSettings | None = None) -> None:
        settings = settings or ComparativeDomainModelBuilderSettings.default()
        candidates: list[tuple[bool, ComparativeDomainModelBuilderPort]] = [
            (settings.group_context_aggregation_builder_enabled, GroupContextAggregationBuilder()),
        ]
        for enabled, builder in candidates:
            if enabled:
                self.register(builder)

    def get(self, name: str) -> ComparativeDomainModelBuilderPort | None:
        return self._builders_by_name.get(name)

    def require(self, name: str) -> ComparativeDomainModelBuilderPort:
        builder = self.get(name)
        if builder is None:
            raise DomainModelBuilderNotFoundError(f"Constructor no registrado: {name}")
        return builder

    def all_builders(self) -> tuple[ComparativeDomainModelBuilderPort, ...]:
        return tuple(self._builders_ordered)

    def count(self) -> int:
        return len(self._builders_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [builder.snapshot() for builder in self._builders_ordered]
