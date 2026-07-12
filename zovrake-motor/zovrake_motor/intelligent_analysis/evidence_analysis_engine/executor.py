"""Ejecutor de analizadores del Evidence Analysis Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.analyzers import (
    build_evidence_catalog,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import EvidenceAnalysisStatus
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisIncident,
    EvidenceAnalysisResult,
    ModelEvidenceProfile,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.registry import (
    EvidenceAnalyzerRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings


class EvidenceAnalysisExecutor:
    """Coordina la ejecución secuencial de analizadores sin modificar el catálogo definitivo."""

    def __init__(self, registry: EvidenceAnalyzerRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: DefinitiveComparativeModelCatalogView,
        *,
        settings: EvidenceAnalysisEngineSettings,
    ) -> EvidenceAnalysisResult:
        profiles: list[ModelEvidenceProfile] = []
        incidents: list[EvidenceAnalysisIncident] = []
        observations: list[str] = []
        sequence = 0

        for analyzer in self._registry.all_analyzers():
            result = analyzer.analyze(
                catalog_view,
                settings=settings,
                start_sequence=sequence + 1,
            )
            profiles.extend(result.profiles)
            observations.extend(result.technical_observations)
            sequence += sum(len(profile.evidence_records) for profile in result.profiles)

        if len(profiles) > settings.max_models_per_process:
            incidents.append(
                EvidenceAnalysisIncident(
                    analyzer_name="evidence_analysis_executor",
                    message=(
                        f"Se analizaron {len(profiles)} modelos; "
                        f"límite configurado: {settings.max_models_per_process}"
                    ),
                    severity="warning",
                ),
            )
            profiles = profiles[: settings.max_models_per_process]

        catalog = build_evidence_catalog(
            catalog_view=catalog_view,
            profiles=tuple(profiles),
            settings=settings,
        )

        evidence_records_count = sum(len(profile.evidence_records) for profile in profiles)
        missing_records_count = sum(
            len(profile.missing_evidence_records) for profile in profiles
        )

        status = (
            EvidenceAnalysisStatus.ANALYZED
            if profiles and evidence_records_count > 0
            else EvidenceAnalysisStatus.SKIPPED
        )
        if profiles and missing_records_count > 0 and evidence_records_count > 0:
            status = EvidenceAnalysisStatus.PARTIAL

        observations.extend(
            (
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
                f"profiles_analyzed={len(profiles)}",
                f"evidence_records_identified={evidence_records_count}",
                f"missing_evidence_records_identified={missing_records_count}",
            ),
        )

        return EvidenceAnalysisResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            evidence_records_count=evidence_records_count,
            missing_evidence_records_count=missing_records_count,
            definitive_catalog_preserved=True,
            source_data_preserved=catalog_view.source_data_preserved,
            analyzers_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
