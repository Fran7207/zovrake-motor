"""Ejecutor de evaluadores del Consistency Evaluation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyEvaluationStatus,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.evaluators import (
    build_consistency_catalog,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationIncident,
    ConsistencyEvaluationResult,
    ModelConsistencyProfile,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.registry import (
    ConsistencyEvaluatorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings


class ConsistencyEvaluationExecutor:
    """Coordina la ejecución secuencial de evaluadores sin modificar el catálogo de evidencias."""

    def __init__(self, registry: ConsistencyEvaluatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: EvidenceAnalysisCatalogView,
        *,
        settings: ConsistencyEvaluationEngineSettings,
    ) -> ConsistencyEvaluationResult:
        profiles: list[ModelConsistencyProfile] = []
        incidents: list[ConsistencyEvaluationIncident] = []
        observations: list[str] = []
        sequence = 0

        for evaluator in self._registry.all_evaluators():
            result = evaluator.evaluate(
                catalog_view,
                settings=settings,
                start_sequence=sequence + 1,
            )
            profiles.extend(result.profiles)
            observations.extend(result.technical_observations)
            sequence += sum(len(profile.inconsistencies) for profile in result.profiles)

        if len(profiles) > settings.max_profiles_per_process:
            incidents.append(
                ConsistencyEvaluationIncident(
                    evaluator_name="consistency_evaluation_executor",
                    message=(
                        f"Se evaluaron {len(profiles)} perfiles; "
                        f"límite configurado: {settings.max_profiles_per_process}"
                    ),
                    severity="warning",
                ),
            )
            profiles = profiles[: settings.max_profiles_per_process]

        catalog = build_consistency_catalog(
            catalog_view=catalog_view,
            profiles=tuple(profiles),
            settings=settings,
        )

        inconsistencies_count = sum(len(profile.inconsistencies) for profile in profiles)
        sufficient_profiles_count = sum(
            1 for profile in profiles if profile.sufficiency.sufficient_for_reasoning
        )
        insufficient_profiles_count = len(profiles) - sufficient_profiles_count

        status = (
            ConsistencyEvaluationStatus.EVALUATED
            if profiles
            else ConsistencyEvaluationStatus.SKIPPED
        )
        if profiles and inconsistencies_count > 0:
            status = ConsistencyEvaluationStatus.PARTIAL

        observations.extend(
            (
                "evidence_catalog_preserved=True",
                "definitive_model_unaccessed=True",
                f"profiles_evaluated={len(profiles)}",
                f"inconsistencies_detected={inconsistencies_count}",
                f"sufficient_profiles={sufficient_profiles_count}",
                f"insufficient_profiles={insufficient_profiles_count}",
            ),
        )

        return ConsistencyEvaluationResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            inconsistencies_count=inconsistencies_count,
            sufficient_profiles_count=sufficient_profiles_count,
            insufficient_profiles_count=insufficient_profiles_count,
            evidence_catalog_preserved=True,
            source_data_preserved=catalog_view.source_data_preserved,
            evaluators_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
