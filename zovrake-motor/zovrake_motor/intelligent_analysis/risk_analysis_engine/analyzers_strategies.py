"""Analizadores especializados del Risk Analysis Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.risk_analysis_engine.analyzers import (
    identify_profile_risks,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.enums import (
    RiskAnalyzerStrategyType,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.gateway import (
    EvidenceAndConsistencyInputView,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import AnalyzerResult
from zovrake_motor.intelligent_analysis.risk_analysis_engine.port import RiskAnalyzerPort
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings


class OrganizedEvidenceConsistencyRiskAnalyzer(RiskAnalyzerPort):
    """
    Analiza riesgos a partir de evidencias organizadas y evaluación de consistencia.

    Identifica y clasifica sin interpretar ni modificar la información original.
    """

    @property
    def analyzer_name(self) -> str:
        return "organized_evidence_consistency_risk_analyzer"

    @property
    def analyzer_label(self) -> str:
        return "Analizador de Riesgos — Evidencias y Consistencia"

    @property
    def analyzer_type(self) -> str:
        return RiskAnalyzerStrategyType.ORGANIZED_EVIDENCE_CONSISTENCY.value

    def analyze(
        self,
        input_view: EvidenceAndConsistencyInputView,
        *,
        settings: RiskAnalysisEngineSettings,
        start_sequence: int,
    ) -> AnalyzerResult:
        profiles = []
        sequence = start_sequence

        consistency_by_model = {
            profile.definitive_model_id: profile
            for profile in input_view.consistency_catalog.profiles
        }

        for evidence_profile in input_view.evidence_catalog.profiles:
            consistency_profile = consistency_by_model.get(evidence_profile.definitive_model_id)
            if consistency_profile is None:
                continue
            profile, sequence = identify_profile_risks(
                input_view=input_view,
                evidence_profile=evidence_profile,
                consistency_profile=consistency_profile,
                settings=settings,
                start_sequence=sequence,
            )
            profiles.append(profile)

        total_risks = sum(len(profile.risks) for profile in profiles)

        return AnalyzerResult(
            analyzer_type=self.analyzer_type,
            analyzer_name=self.analyzer_name,
            profiles=tuple(profiles),
            technical_observations=(
                f"analyzer_type={self.analyzer_type}",
                f"profiles_analyzed={len(profiles)}",
                f"risks_identified={total_risks}",
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "definitive_model_unaccessed=True",
            ),
        )
