"""Generadores especializados del Explanation Generation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationGeneratorStrategyType,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ExplanationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.generators import (
    generate_model_explanation_profile,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import GeneratorResult
from zovrake_motor.intelligent_analysis.explanation_generation_engine.port import (
    ExplanationGeneratorPort,
)
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings


class OrganizedAnalysisExplanationGenerator(ExplanationGeneratorPort):
    """
    Genera explicaciones estructuradas a partir de evidencias, consistencia,
    riesgos y contexto — sin emitir conclusiones ni recomendaciones.
    """

    @property
    def generator_name(self) -> str:
        return "organized_analysis_explanation_generator"

    @property
    def generator_label(self) -> str:
        return "Generador de Explicaciones — Análisis Organizado"

    @property
    def generator_type(self) -> str:
        return ExplanationGeneratorStrategyType.ORGANIZED_ANALYSIS_EXPLANATION.value

    def generate(
        self,
        input_view: ExplanationGenerationInputView,
        *,
        settings: ExplanationGenerationEngineSettings,
        start_sequence: int,
    ) -> GeneratorResult:
        profiles = []
        sequence = start_sequence

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

        for evidence_profile in input_view.evidence_catalog.profiles:
            consistency_profile = consistency_by_model.get(evidence_profile.definitive_model_id)
            risk_profile = risk_by_model.get(evidence_profile.definitive_model_id)
            context_profile = context_by_model.get(evidence_profile.definitive_model_id)

            profile, sequence = generate_model_explanation_profile(
                input_view=input_view,
                evidence_profile=evidence_profile,
                consistency_profile=consistency_profile,
                risk_profile=risk_profile,
                context_profile=context_profile,
                settings=settings,
                start_sequence=sequence,
            )
            profiles.append(profile)

        total_segments = sum(len(profile.segments) for profile in profiles)

        return GeneratorResult(
            generator_type=self.generator_type,
            generator_name=self.generator_name,
            profiles=tuple(profiles),
            technical_observations=(
                f"generator_type={self.generator_type}",
                f"profiles_generated={len(profiles)}",
                f"explanation_segments_generated={total_segments}",
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "context_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
            ),
        )
