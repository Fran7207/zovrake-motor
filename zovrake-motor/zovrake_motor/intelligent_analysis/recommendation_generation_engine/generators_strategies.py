"""Generadores especializados del Recommendation Generation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.enums import (
    RecommendationGeneratorStrategyType,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    RecommendationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.generators import (
    generate_model_recommendation_profile,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import GeneratorResult
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.port import (
    RecommendationGeneratorPort,
)
from zovrake_motor.config.categories.intelligent_analysis import RecommendationGenerationEngineSettings


class OrganizedEvidenceRecommendationGenerator(RecommendationGeneratorPort):
    """
    Genera recomendaciones fundamentadas a partir de evidencias, consistencia,
    riesgos, contexto y explicaciones — sin sustituir el criterio humano.
    """

    @property
    def generator_name(self) -> str:
        return "organized_evidence_recommendation_generator"

    @property
    def generator_label(self) -> str:
        return "Generador de Recomendaciones — Evidencias Organizadas"

    @property
    def generator_type(self) -> str:
        return RecommendationGeneratorStrategyType.ORGANIZED_EVIDENCE_RECOMMENDATION.value

    def generate(
        self,
        input_view: RecommendationGenerationInputView,
        *,
        settings: RecommendationGenerationEngineSettings,
    ) -> GeneratorResult:
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

        profiles = []
        for evidence_profile in input_view.evidence_catalog.profiles:
            profile = generate_model_recommendation_profile(
                input_view=input_view,
                evidence_profile=evidence_profile,
                consistency_profile=consistency_by_model.get(evidence_profile.definitive_model_id),
                risk_profile=risk_by_model.get(evidence_profile.definitive_model_id),
                context_profile=context_by_model.get(evidence_profile.definitive_model_id),
                explanation_profile=explanation_by_model.get(evidence_profile.definitive_model_id),
                settings=settings,
            )
            profiles.append(profile)

        return GeneratorResult(
            generator_type=self.generator_type,
            generator_name=self.generator_name,
            profiles=tuple(profiles),
            technical_observations=(
                f"generator_type={self.generator_type}",
                f"profiles_generated={len(profiles)}",
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "context_catalog_preserved=True",
                "explanation_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
            ),
        )
