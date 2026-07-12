"""Registro centralizado de analizadores del EAE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.analyzers_strategies import (
    DefinitiveModelEvidenceAnalyzer,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.exceptions import (
    EvidenceAnalyzerNotFoundError,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.port import EvidenceAnalyzerPort
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings


class EvidenceAnalyzerRegistry:
    """
    Registro único de analizadores de evidencias.

    Todo analizador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._analyzers_by_name: dict[str, EvidenceAnalyzerPort] = {}
        self._analyzers_ordered: list[EvidenceAnalyzerPort] = []

    def register(self, analyzer: EvidenceAnalyzerPort) -> None:
        if analyzer.analyzer_name in self._analyzers_by_name:
            raise ValueError(f"Analizador ya registrado: {analyzer.analyzer_name}")
        self._analyzers_by_name[analyzer.analyzer_name] = analyzer
        self._analyzers_ordered.append(analyzer)

    def register_defaults(self, *, settings: EvidenceAnalysisEngineSettings | None = None) -> None:
        settings = settings or EvidenceAnalysisEngineSettings.default()
        candidates: list[tuple[bool, EvidenceAnalyzerPort]] = [
            (settings.definitive_model_evidence_analyzer_enabled, DefinitiveModelEvidenceAnalyzer()),
        ]
        for enabled, analyzer in candidates:
            if enabled:
                self.register(analyzer)

    def get(self, name: str) -> EvidenceAnalyzerPort | None:
        return self._analyzers_by_name.get(name)

    def require(self, name: str) -> EvidenceAnalyzerPort:
        analyzer = self.get(name)
        if analyzer is None:
            raise EvidenceAnalyzerNotFoundError(f"Analizador no registrado: {name}")
        return analyzer

    def all_analyzers(self) -> tuple[EvidenceAnalyzerPort, ...]:
        return tuple(self._analyzers_ordered)

    def count(self) -> int:
        return len(self._analyzers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [analyzer.snapshot() for analyzer in self._analyzers_ordered]
