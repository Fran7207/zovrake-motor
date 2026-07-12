"""Analizadores especializados del Evidence Analysis Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.analyzers import (
    build_model_evidence_profile,
    collect_model_evidence,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import (
    EvidenceAnalyzerStrategyType,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import AnalyzerResult
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.port import EvidenceAnalyzerPort
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings


class DefinitiveModelEvidenceAnalyzer(EvidenceAnalyzerPort):
    """
    Analiza evidencias presentes en cada Modelo Comparativo Definitivo.

    Identifica y organiza sin interpretar ni modificar la información original.
    """

    @property
    def analyzer_name(self) -> str:
        return "definitive_model_evidence_analyzer"

    @property
    def analyzer_label(self) -> str:
        return "Analizador de Evidencias — Modelo Comparativo Definitivo"

    @property
    def analyzer_type(self) -> str:
        return EvidenceAnalyzerStrategyType.DEFINITIVE_MODEL.value

    def analyze(
        self,
        catalog_view: DefinitiveComparativeModelCatalogView,
        *,
        settings: EvidenceAnalysisEngineSettings,
        start_sequence: int,
    ) -> AnalyzerResult:
        profiles = []
        sequence = start_sequence

        for model_view in catalog_view.models:
            evidence_records, missing_records, sequence = collect_model_evidence(
                catalog_view=catalog_view,
                model_view=model_view,
                settings=settings,
                start_sequence=sequence,
            )
            profiles.append(
                build_model_evidence_profile(
                    catalog_view=catalog_view,
                    model_view=model_view,
                    evidence_records=tuple(evidence_records),
                    missing_evidence_records=tuple(missing_records),
                ),
            )

        total_evidence = sum(len(profile.evidence_records) for profile in profiles)
        total_missing = sum(len(profile.missing_evidence_records) for profile in profiles)

        return AnalyzerResult(
            analyzer_type=self.analyzer_type,
            analyzer_name=self.analyzer_name,
            profiles=tuple(profiles),
            technical_observations=(
                f"analyzer_type={self.analyzer_type}",
                f"models_analyzed={len(profiles)}",
                f"evidence_records_identified={total_evidence}",
                f"missing_evidence_records_identified={total_missing}",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
            ),
        )
