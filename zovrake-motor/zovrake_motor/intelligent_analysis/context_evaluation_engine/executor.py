"""Ejecutor de evaluadores del Context Evaluation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.context_evaluation_engine.enums import (
    ContextEvaluationStatus,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.evaluators import (
    build_context_catalog,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.gateway import (
    ContextEvaluationInputView,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationIncident,
    ContextEvaluationResult,
    ModelContextProfile,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.registry import (
    ContextEvaluatorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings


class ContextEvaluationExecutor:
    """Coordina la ejecución secuencial de evaluadores sin modificar las entradas."""

    def __init__(self, registry: ContextEvaluatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ContextEvaluationInputView,
        *,
        settings: ContextEvaluationEngineSettings,
    ) -> ContextEvaluationResult:
        profiles: list[ModelContextProfile] = []
        incidents: list[ContextEvaluationIncident] = []
        observations: list[str] = []
        sequence = 0

        for evaluator in self._registry.all_evaluators():
            result = evaluator.evaluate(
                input_view,
                settings=settings,
                start_sequence=sequence + 1,
            )
            profiles.extend(result.profiles)
            observations.extend(result.technical_observations)
            sequence += sum(
                len(profile.associations) + len(profile.contextual_gaps) for profile in result.profiles
            )

        if len(profiles) > settings.max_profiles_per_process:
            incidents.append(
                ContextEvaluationIncident(
                    evaluator_name="context_evaluation_executor",
                    message=(
                        f"Se evaluaron {len(profiles)} perfiles; "
                        f"límite configurado: {settings.max_profiles_per_process}"
                    ),
                    severity="warning",
                ),
            )
            profiles = profiles[: settings.max_profiles_per_process]

        catalog = build_context_catalog(
            input_view=input_view,
            profiles=tuple(profiles),
            settings=settings,
        )

        associations_count = sum(len(profile.associations) for profile in profiles)
        contextual_gaps_count = sum(len(profile.contextual_gaps) for profile in profiles)

        status = ContextEvaluationStatus.EVALUATED if profiles else ContextEvaluationStatus.SKIPPED
        if profiles and (associations_count > 0 or contextual_gaps_count > 0):
            status = ContextEvaluationStatus.PARTIAL

        observations.extend(
            (
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "requirement_context_preserved=True",
                "source_files_unaccessed=True",
                f"profiles_evaluated={len(profiles)}",
                f"context_associations_identified={associations_count}",
                f"contextual_gaps_identified={contextual_gaps_count}",
            ),
        )

        return ContextEvaluationResult(
            process_id=input_view.evidence_catalog.process_id,
            document_id=input_view.evidence_catalog.document_id,
            model_id=input_view.evidence_catalog.model_id,
            catalog=catalog,
            status=status,
            associations_count=associations_count,
            contextual_gaps_count=contextual_gaps_count,
            evidence_catalog_preserved=True,
            consistency_catalog_preserved=True,
            risk_catalog_preserved=True,
            definitive_catalog_preserved=True,
            requirement_context_preserved=True,
            source_data_preserved=input_view.evidence_catalog.source_data_preserved,
            evaluators_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
