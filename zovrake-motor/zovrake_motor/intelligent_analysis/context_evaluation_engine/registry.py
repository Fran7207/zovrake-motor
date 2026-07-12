"""Registro centralizado de evaluadores del CxEE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.context_evaluation_engine.evaluators_strategies import (
    OrganizedEvidenceRiskContextEvaluator,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.exceptions import (
    ContextEvaluatorNotFoundError,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.port import ContextEvaluatorPort
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings


class ContextEvaluatorRegistry:
    """
    Registro único de evaluadores contextuales.

    Todo evaluador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._evaluators_by_name: dict[str, ContextEvaluatorPort] = {}
        self._evaluators_ordered: list[ContextEvaluatorPort] = []

    def register(self, evaluator: ContextEvaluatorPort) -> None:
        if evaluator.evaluator_name in self._evaluators_by_name:
            raise ValueError(f"Evaluador ya registrado: {evaluator.evaluator_name}")
        self._evaluators_by_name[evaluator.evaluator_name] = evaluator
        self._evaluators_ordered.append(evaluator)

    def register_defaults(
        self,
        *,
        settings: ContextEvaluationEngineSettings | None = None,
    ) -> None:
        settings = settings or ContextEvaluationEngineSettings.default()
        candidates: list[tuple[bool, ContextEvaluatorPort]] = [
            (
                settings.organized_context_evaluator_enabled,
                OrganizedEvidenceRiskContextEvaluator(),
            ),
        ]
        for enabled, evaluator in candidates:
            if enabled:
                self.register(evaluator)

    def get(self, name: str) -> ContextEvaluatorPort | None:
        return self._evaluators_by_name.get(name)

    def require(self, name: str) -> ContextEvaluatorPort:
        evaluator = self.get(name)
        if evaluator is None:
            raise ContextEvaluatorNotFoundError(f"Evaluador no registrado: {name}")
        return evaluator

    def all_evaluators(self) -> tuple[ContextEvaluatorPort, ...]:
        return tuple(self._evaluators_ordered)

    def count(self) -> int:
        return len(self._evaluators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [evaluator.snapshot() for evaluator in self._evaluators_ordered]
