"""Evaluadores especializados del Consistency Evaluation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyEvaluatorStrategyType,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.evaluators import (
    evaluate_profile_consistency,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import EvaluatorResult
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.port import (
    ConsistencyEvaluatorPort,
)
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings


class OrganizedEvidenceConsistencyEvaluator(ConsistencyEvaluatorPort):
    """
    Evalúa la consistencia de evidencias organizadas por el EAE.

    Detecta inconsistencias y evalúa suficiencia sin modificar la información original.
    """

    @property
    def evaluator_name(self) -> str:
        return "organized_evidence_consistency_evaluator"

    @property
    def evaluator_label(self) -> str:
        return "Evaluador de Consistencia — Evidencias Organizadas"

    @property
    def evaluator_type(self) -> str:
        return ConsistencyEvaluatorStrategyType.ORGANIZED_EVIDENCE.value

    def evaluate(
        self,
        catalog_view: EvidenceAnalysisCatalogView,
        *,
        settings: ConsistencyEvaluationEngineSettings,
        start_sequence: int,
    ) -> EvaluatorResult:
        profiles = []
        sequence = start_sequence

        for profile_view in catalog_view.profiles:
            profile, sequence = evaluate_profile_consistency(
                catalog_view=catalog_view,
                profile_view=profile_view,
                settings=settings,
                start_sequence=sequence,
            )
            profiles.append(profile)

        total_inconsistencies = sum(len(profile.inconsistencies) for profile in profiles)
        sufficient_count = sum(
            1 for profile in profiles if profile.sufficiency.sufficient_for_reasoning
        )

        return EvaluatorResult(
            evaluator_type=self.evaluator_type,
            evaluator_name=self.evaluator_name,
            profiles=tuple(profiles),
            technical_observations=(
                f"evaluator_type={self.evaluator_type}",
                f"profiles_evaluated={len(profiles)}",
                f"inconsistencies_detected={total_inconsistencies}",
                f"sufficient_profiles={sufficient_count}",
                "evidence_catalog_preserved=True",
                "definitive_model_unaccessed=True",
            ),
        )
