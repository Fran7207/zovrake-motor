"""Registro centralizado de asociadores del CAE-Context."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.context_association.associators import UniformGroupContextAssociator
from zovrake_motor.classification.context_association.exceptions import ContextAssociatorNotFoundError
from zovrake_motor.classification.context_association.port import ContextAssociatorPort
from zovrake_motor.config.categories.classification import ContextAssociationSettings


class ContextAssociatorRegistry:
    """Registro único de asociadores de contexto."""

    def __init__(self) -> None:
        self._associators_by_name: dict[str, ContextAssociatorPort] = {}
        self._associators_ordered: list[ContextAssociatorPort] = []

    def register(self, associator: ContextAssociatorPort) -> None:
        if associator.associator_name in self._associators_by_name:
            raise ValueError(f"Asociador ya registrado: {associator.associator_name}")
        self._associators_by_name[associator.associator_name] = associator
        self._associators_ordered.append(associator)

    def register_defaults(self, *, settings: ContextAssociationSettings | None = None) -> None:
        settings = settings or ContextAssociationSettings.default()
        candidates: list[tuple[bool, ContextAssociatorPort]] = [
            (settings.uniform_group_context_associator_enabled, UniformGroupContextAssociator()),
        ]
        for enabled, associator in candidates:
            if enabled:
                self.register(associator)

    def get(self, name: str) -> ContextAssociatorPort | None:
        return self._associators_by_name.get(name)

    def require(self, name: str) -> ContextAssociatorPort:
        associator = self.get(name)
        if associator is None:
            raise ContextAssociatorNotFoundError(f"Asociador no registrado: {name}")
        return associator

    def all_associators(self) -> tuple[ContextAssociatorPort, ...]:
        return tuple(self._associators_ordered)

    def count(self) -> int:
        return len(self._associators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [associator.snapshot() for associator in self._associators_ordered]
