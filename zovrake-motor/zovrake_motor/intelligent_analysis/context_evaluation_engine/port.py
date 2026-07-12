"""Contrato de evaluadores contextuales del CxEE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.intelligent_analysis.context_evaluation_engine.gateway import (
    ContextEvaluationInputView,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import EvaluatorResult
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings


class ContextEvaluatorPort(ABC):
    """Contrato base para evaluadores contextuales."""

    @property
    @abstractmethod
    def evaluator_name(self) -> str:
        """Identificador único del evaluador."""

    @property
    @abstractmethod
    def evaluator_label(self) -> str:
        """Etiqueta descriptiva del evaluador."""

    @property
    @abstractmethod
    def evaluator_type(self) -> str:
        """Tipo de estrategia de evaluación."""

    @abstractmethod
    def evaluate(
        self,
        input_view: ContextEvaluationInputView,
        *,
        settings: ContextEvaluationEngineSettings,
        start_sequence: int,
    ) -> EvaluatorResult:
        """Evalúa contexto sin modificar las entradas de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "evaluator_name": self.evaluator_name,
            "evaluator_label": self.evaluator_label,
            "evaluator_type": self.evaluator_type,
        }
