"""Contrato de evaluadores de consistencia del CEE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import EvaluatorResult
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings


class ConsistencyEvaluatorPort(ABC):
    """Contrato base para evaluadores de consistencia."""

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
        catalog_view: EvidenceAnalysisCatalogView,
        *,
        settings: ConsistencyEvaluationEngineSettings,
        start_sequence: int,
    ) -> EvaluatorResult:
        """Evalúa consistencia sin modificar el catálogo de evidencias."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "evaluator_name": self.evaluator_name,
            "evaluator_label": self.evaluator_label,
            "evaluator_type": self.evaluator_type,
        }
