"""Contrato de analizadores de riesgos del RAE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.intelligent_analysis.risk_analysis_engine.gateway import (
    EvidenceAndConsistencyInputView,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import AnalyzerResult
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings


class RiskAnalyzerPort(ABC):
    """Contrato base para analizadores de riesgos."""

    @property
    @abstractmethod
    def analyzer_name(self) -> str:
        """Identificador único del analizador."""

    @property
    @abstractmethod
    def analyzer_label(self) -> str:
        """Etiqueta descriptiva del analizador."""

    @property
    @abstractmethod
    def analyzer_type(self) -> str:
        """Tipo de estrategia de análisis."""

    @abstractmethod
    def analyze(
        self,
        input_view: EvidenceAndConsistencyInputView,
        *,
        settings: RiskAnalysisEngineSettings,
        start_sequence: int,
    ) -> AnalyzerResult:
        """Identifica y clasifica riesgos sin modificar las entradas de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "analyzer_name": self.analyzer_name,
            "analyzer_label": self.analyzer_label,
            "analyzer_type": self.analyzer_type,
        }
