"""Registro centralizado de evaluadores del CEE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.evaluators_strategies import (
    OrganizedEvidenceConsistencyEvaluator,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.exceptions import (
    ConsistencyEvaluatorNotFoundError,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.port import (
    ConsistencyEvaluatorPort,
)
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings


class ConsistencyEvaluatorRegistry:
    """
    Registro único de evaluadores de consistencia.

    Todo evaluador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._evaluators_by_name: dict[str, ConsistencyEvaluatorPort] = {}
        self._evaluators_ordered: list[ConsistencyEvaluatorPort] = []

    def register(self, evaluator: ConsistencyEvaluatorPort) -> None:
        if evaluator.evaluator_name in self._evaluators_by_name:
            raise ValueError(f"Evaluador ya registrado: {evaluator.evaluator_name}")
        self._evaluators_by_name[evaluator.evaluator_name] = evaluator
        self._evaluators_ordered.append(evaluator)

    def register_defaults(
        self,
        *,
        settings: ConsistencyEvaluationEngineSettings | None = None,
    ) -> None:
        settings = settings or ConsistencyEvaluationEngineSettings.default()
        candidates: list[tuple[bool, ConsistencyEvaluatorPort]] = [
            (settings.organized_evidence_evaluator_enabled, OrganizedEvidenceConsistencyEvaluator()),
        ]
        for enabled, evaluator in candidates:
            if enabled:
                self.register(evaluator)

    def get(self, name: str) -> ConsistencyEvaluatorPort | None:
        return self._evaluators_by_name.get(name)

    def require(self, name: str) -> ConsistencyEvaluatorPort:
        evaluator = self.get(name)
        if evaluator is None:
            raise ConsistencyEvaluatorNotFoundError(f"Evaluador no registrado: {name}")
        return evaluator

    def all_evaluators(self) -> tuple[ConsistencyEvaluatorPort, ...]:
        return tuple(self._evaluators_ordered)

    def count(self) -> int:
        return len(self._evaluators_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [evaluator.snapshot() for evaluator in self._evaluators_ordered]
