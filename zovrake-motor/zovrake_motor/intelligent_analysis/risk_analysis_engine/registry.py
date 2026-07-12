"""Registro centralizado de analizadores del RAE."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.risk_analysis_engine.analyzers_strategies import (
    OrganizedEvidenceConsistencyRiskAnalyzer,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.exceptions import (
    RiskAnalyzerNotFoundError,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.port import RiskAnalyzerPort
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings


class RiskAnalyzerRegistry:
    """
    Registro único de analizadores de riesgos.

    Todo analizador debe registrarse exclusivamente desde este punto.
    """

    def __init__(self) -> None:
        self._analyzers_by_name: dict[str, RiskAnalyzerPort] = {}
        self._analyzers_ordered: list[RiskAnalyzerPort] = []

    def register(self, analyzer: RiskAnalyzerPort) -> None:
        if analyzer.analyzer_name in self._analyzers_by_name:
            raise ValueError(f"Analizador ya registrado: {analyzer.analyzer_name}")
        self._analyzers_by_name[analyzer.analyzer_name] = analyzer
        self._analyzers_ordered.append(analyzer)

    def register_defaults(self, *, settings: RiskAnalysisEngineSettings | None = None) -> None:
        settings = settings or RiskAnalysisEngineSettings.default()
        candidates: list[tuple[bool, RiskAnalyzerPort]] = [
            (
                settings.organized_evidence_risk_analyzer_enabled,
                OrganizedEvidenceConsistencyRiskAnalyzer(),
            ),
        ]
        for enabled, analyzer in candidates:
            if enabled:
                self.register(analyzer)

    def get(self, name: str) -> RiskAnalyzerPort | None:
        return self._analyzers_by_name.get(name)

    def require(self, name: str) -> RiskAnalyzerPort:
        analyzer = self.get(name)
        if analyzer is None:
            raise RiskAnalyzerNotFoundError(f"Analizador no registrado: {name}")
        return analyzer

    def all_analyzers(self) -> tuple[RiskAnalyzerPort, ...]:
        return tuple(self._analyzers_ordered)

    def count(self) -> int:
        return len(self._analyzers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [analyzer.snapshot() for analyzer in self._analyzers_ordered]
