"""Ejecutor de analizadores del Risk Analysis Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.risk_analysis_engine.analyzers import build_risk_catalog
from zovrake_motor.intelligent_analysis.risk_analysis_engine.enums import RiskAnalysisStatus
from zovrake_motor.intelligent_analysis.risk_analysis_engine.gateway import (
    EvidenceAndConsistencyInputView,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    ModelRiskProfile,
    RiskAnalysisIncident,
    RiskAnalysisResult,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.registry import RiskAnalyzerRegistry
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings


class RiskAnalysisExecutor:
    """Coordina la ejecución secuencial de analizadores sin modificar las entradas."""

    def __init__(self, registry: RiskAnalyzerRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: EvidenceAndConsistencyInputView,
        *,
        settings: RiskAnalysisEngineSettings,
    ) -> RiskAnalysisResult:
        profiles: list[ModelRiskProfile] = []
        incidents: list[RiskAnalysisIncident] = []
        observations: list[str] = []
        sequence = 0

        for analyzer in self._registry.all_analyzers():
            result = analyzer.analyze(
                input_view,
                settings=settings,
                start_sequence=sequence + 1,
            )
            profiles.extend(result.profiles)
            observations.extend(result.technical_observations)
            sequence += sum(len(profile.risks) for profile in result.profiles)

        if len(profiles) > settings.max_profiles_per_process:
            incidents.append(
                RiskAnalysisIncident(
                    analyzer_name="risk_analysis_executor",
                    message=(
                        f"Se analizaron {len(profiles)} perfiles; "
                        f"límite configurado: {settings.max_profiles_per_process}"
                    ),
                    severity="warning",
                ),
            )
            profiles = profiles[: settings.max_profiles_per_process]

        catalog = build_risk_catalog(
            input_view=input_view,
            profiles=tuple(profiles),
            settings=settings,
        )

        risks_count = sum(len(profile.risks) for profile in profiles)

        status = RiskAnalysisStatus.ANALYZED if profiles else RiskAnalysisStatus.SKIPPED
        if profiles and risks_count > 0:
            status = RiskAnalysisStatus.PARTIAL

        observations.extend(
            (
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "definitive_model_unaccessed=True",
                f"profiles_analyzed={len(profiles)}",
                f"risks_identified={risks_count}",
            ),
        )

        return RiskAnalysisResult(
            process_id=input_view.evidence_catalog.process_id,
            document_id=input_view.evidence_catalog.document_id,
            model_id=input_view.evidence_catalog.model_id,
            catalog=catalog,
            status=status,
            risks_count=risks_count,
            evidence_catalog_preserved=True,
            consistency_catalog_preserved=True,
            source_data_preserved=input_view.evidence_catalog.source_data_preserved,
            analyzers_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
