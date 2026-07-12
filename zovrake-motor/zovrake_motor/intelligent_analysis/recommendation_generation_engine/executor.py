"""Ejecutor de generadores del Recommendation Generation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.enums import (
    RecommendationGenerationStatus,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    RecommendationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.generators import (
    build_recommendation_catalog,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    ModelRecommendationProfile,
    RecommendationGenerationIncident,
    RecommendationGenerationResult,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.registry import (
    RecommendationGeneratorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import RecommendationGenerationEngineSettings


class RecommendationGenerationExecutor:
    """Coordina la ejecución secuencial de generadores sin modificar las entradas."""

    def __init__(self, registry: RecommendationGeneratorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: RecommendationGenerationInputView,
        *,
        settings: RecommendationGenerationEngineSettings,
    ) -> RecommendationGenerationResult:
        profiles: list[ModelRecommendationProfile] = []
        incidents: list[RecommendationGenerationIncident] = []
        observations: list[str] = []

        for generator in self._registry.all_generators():
            result = generator.generate(input_view, settings=settings)
            profiles.extend(result.profiles)
            observations.extend(result.technical_observations)

        if len(profiles) > settings.max_profiles_per_process:
            incidents.append(
                RecommendationGenerationIncident(
                    generator_name="recommendation_generation_executor",
                    message=(
                        f"Se generaron {len(profiles)} perfiles; "
                        f"límite configurado: {settings.max_profiles_per_process}"
                    ),
                    severity="warning",
                ),
            )
            profiles = profiles[: settings.max_profiles_per_process]

        catalog = build_recommendation_catalog(
            input_view=input_view,
            profiles=tuple(profiles),
            settings=settings,
        )

        status = RecommendationGenerationStatus.GENERATED if profiles else RecommendationGenerationStatus.SKIPPED

        observations.extend(
            (
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "context_catalog_preserved=True",
                "explanation_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
                f"profiles_generated={len(profiles)}",
            ),
        )

        return RecommendationGenerationResult(
            process_id=input_view.evidence_catalog.process_id,
            document_id=input_view.evidence_catalog.document_id,
            model_id=input_view.evidence_catalog.model_id,
            catalog=catalog,
            status=status,
            recommendations_count=len(profiles),
            evidence_catalog_preserved=True,
            consistency_catalog_preserved=True,
            risk_catalog_preserved=True,
            context_catalog_preserved=True,
            explanation_catalog_preserved=True,
            definitive_catalog_preserved=True,
            source_data_preserved=input_view.evidence_catalog.source_data_preserved,
            generators_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
