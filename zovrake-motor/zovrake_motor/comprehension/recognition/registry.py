"""Registro centralizado de estrategias de reconocimiento."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.recognition.exceptions import RecognitionStrategyNotFoundError
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.strategies import (
    ExtensionRecognitionStrategy,
    MagicNumberRecognitionStrategy,
    MetadataRecognitionStrategy,
    MimeTypeRecognitionStrategy,
)
from zovrake_motor.config.categories.comprehension import DocumentRecognitionSettings


class RecognitionStrategyRegistry:
    """
    Registro único de estrategias de reconocimiento documental.

    Toda estrategia debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._strategies_by_name: dict[str, RecognitionStrategyPort] = {}
        self._strategies_ordered: list[RecognitionStrategyPort] = []

    def register(self, strategy: RecognitionStrategyPort) -> None:
        if strategy.strategy_name in self._strategies_by_name:
            raise ValueError(f"Estrategia ya registrada: {strategy.strategy_name}")
        self._strategies_by_name[strategy.strategy_name] = strategy
        self._strategies_ordered.append(strategy)

    def register_defaults(self, *, settings: DocumentRecognitionSettings | None = None) -> None:
        settings = settings or DocumentRecognitionSettings.default()
        candidates: list[tuple[bool, RecognitionStrategyPort]] = [
            (settings.extension_strategy_enabled, ExtensionRecognitionStrategy()),
            (settings.mime_type_strategy_enabled, MimeTypeRecognitionStrategy()),
            (settings.metadata_strategy_enabled, MetadataRecognitionStrategy()),
            (settings.magic_number_strategy_enabled, MagicNumberRecognitionStrategy()),
        ]
        for enabled, strategy in candidates:
            if enabled:
                self.register(strategy)

    def get(self, name: str) -> RecognitionStrategyPort | None:
        return self._strategies_by_name.get(name)

    def require(self, name: str) -> RecognitionStrategyPort:
        strategy = self.get(name)
        if strategy is None:
            raise RecognitionStrategyNotFoundError(f"Estrategia no registrada: {name}")
        return strategy

    def all_strategies(self) -> tuple[RecognitionStrategyPort, ...]:
        return tuple(self._strategies_ordered)

    def count(self) -> int:
        return len(self._strategies_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [strategy.snapshot() for strategy in self._strategies_ordered]
