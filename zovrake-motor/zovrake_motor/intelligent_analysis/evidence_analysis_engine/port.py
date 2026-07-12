"""Contrato de analizadores de evidencias del EAE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import AnalyzerResult
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings


class EvidenceAnalyzerPort(ABC):
    """Contrato base para analizadores de evidencias."""

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
        catalog_view: DefinitiveComparativeModelCatalogView,
        *,
        settings: EvidenceAnalysisEngineSettings,
        start_sequence: int,
    ) -> AnalyzerResult:
        """Identifica y organiza evidencias sin modificar el catálogo de origen."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "analyzer_name": self.analyzer_name,
            "analyzer_label": self.analyzer_label,
            "analyzer_type": self.analyzer_type,
        }
