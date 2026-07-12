"""Evaluadores especializados del Context Evaluation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.context_evaluation_engine.enums import (
    ContextEvaluatorStrategyType,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.evaluators import (
    evaluate_profile_context,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.gateway import (
    ContextEvaluationInputView,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import EvaluatorResult
from zovrake_motor.intelligent_analysis.context_evaluation_engine.port import ContextEvaluatorPort
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings


class OrganizedEvidenceRiskContextEvaluator(ContextEvaluatorPort):
    """
    Evalúa la relación entre contexto del requerimiento y evidencias organizadas.

    Relaciona contexto con evidencias, riesgos y consistencia sin emitir conclusiones.
    """

    @property
    def evaluator_name(self) -> str:
        return "organized_evidence_risk_context_evaluator"

    @property
    def evaluator_label(self) -> str:
        return "Evaluador Contextual — Evidencias, Consistencia y Riesgos"

    @property
    def evaluator_type(self) -> str:
        return ContextEvaluatorStrategyType.ORGANIZED_EVIDENCE_RISK_CONTEXT.value

    def evaluate(
        self,
        input_view: ContextEvaluationInputView,
        *,
        settings: ContextEvaluationEngineSettings,
        start_sequence: int,
    ) -> EvaluatorResult:
        profiles = []
        sequence = start_sequence

        models_by_id = {
            model.definitive_model_id: model for model in input_view.definitive_catalog.models
        }

        for evidence_profile in input_view.evidence_catalog.profiles:
            model_view = models_by_id.get(evidence_profile.definitive_model_id)
            if model_view is None:
                continue
            profile, sequence = evaluate_profile_context(
                input_view=input_view,
                evidence_profile=evidence_profile,
                model_view=model_view,
                settings=settings,
                start_sequence=sequence,
            )
            profiles.append(profile)

        total_associations = sum(len(profile.associations) for profile in profiles)
        total_gaps = sum(len(profile.contextual_gaps) for profile in profiles)

        return EvaluatorResult(
            evaluator_type=self.evaluator_type,
            evaluator_name=self.evaluator_name,
            profiles=tuple(profiles),
            technical_observations=(
                f"evaluator_type={self.evaluator_type}",
                f"profiles_evaluated={len(profiles)}",
                f"context_associations_identified={total_associations}",
                f"contextual_gaps_identified={total_gaps}",
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "requirement_context_preserved=True",
                "source_files_unaccessed=True",
            ),
        )
