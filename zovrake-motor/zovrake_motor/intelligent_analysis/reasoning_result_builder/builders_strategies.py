"""Constructores especializados del Reasoning Result Builder."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ModelConsistencyProfileView,
    ModelContextProfileView,
    ModelRiskProfileView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    ModelExplanationProfileView,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.builders import (
    build_group_intelligent_analysis_result,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.enums import (
    ReasoningResultBuilderStrategyType,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.gateway import (
    ReasoningResultInputView,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import BuilderResult
from zovrake_motor.intelligent_analysis.reasoning_result_builder.port import ReasoningResultBuilderPort
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings


class OrganizedReasoningResultBuilder(ReasoningResultBuilderPort):
    """Consolida resultados del análisis inteligente por Grupo Comparable."""

    @property
    def builder_name(self) -> str:
        return "organized_reasoning_result_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Resultados — Análisis Organizado"

    @property
    def builder_type(self) -> str:
        return ReasoningResultBuilderStrategyType.ORGANIZED_REASONING_RESULT.value

    def build(
        self,
        input_view: ReasoningResultInputView,
        *,
        settings: ReasoningResultBuilderSettings,
        start_sequence: int,
    ) -> BuilderResult:
        consistency_by_model = {
            profile.definitive_model_id: profile
            for profile in input_view.consistency_catalog.profiles
        }
        risk_by_model = {
            profile.definitive_model_id: profile for profile in input_view.risk_catalog.profiles
        }
        context_by_model = {
            profile.definitive_model_id: profile
            for profile in input_view.context_catalog.profiles
        }
        explanation_by_model = {
            profile.definitive_model_id: profile
            for profile in input_view.explanation_catalog.profiles
        }
        recommendation_by_model = {
            profile.definitive_model_id: profile
            for profile in input_view.recommendation_catalog.profiles
        }

        results = []
        sequence = start_sequence
        for evidence_profile in input_view.evidence_catalog.profiles:
            sequence += 1
            result = build_group_intelligent_analysis_result(
                input_view=input_view,
                evidence_profile=evidence_profile,
                consistency_profile=consistency_by_model.get(evidence_profile.definitive_model_id),
                risk_profile=risk_by_model.get(evidence_profile.definitive_model_id),
                context_profile=context_by_model.get(evidence_profile.definitive_model_id),
                explanation_profile=explanation_by_model.get(evidence_profile.definitive_model_id),
                recommendation_profile=recommendation_by_model.get(
                    evidence_profile.definitive_model_id,
                ),
                settings=settings,
                sequence=sequence,
            )
            results.append(result)

        return BuilderResult(
            builder_type=self.builder_type,
            builder_name=self.builder_name,
            results=tuple(results),
            technical_observations=(
                f"builder_type={self.builder_type}",
                f"results_built={len(results)}",
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "context_catalog_preserved=True",
                "explanation_catalog_preserved=True",
                "recommendation_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
            ),
        )
