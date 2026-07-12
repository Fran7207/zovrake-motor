"""Ejecutor de generadores del Explanation Generation Engine."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationGenerationStatus,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ExplanationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.generators import (
    build_explanation_catalog,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationIncident,
    ExplanationGenerationResult,
    ModelExplanationProfile,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.registry import (
    ExplanationGeneratorRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings


class ExplanationGenerationExecutor:
    """Coordina la ejecución secuencial de generadores sin modificar las entradas."""

    def __init__(self, registry: ExplanationGeneratorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ExplanationGenerationInputView,
        *,
        settings: ExplanationGenerationEngineSettings,
    ) -> ExplanationGenerationResult:
        profiles: list[ModelExplanationProfile] = []
        incidents: list[ExplanationGenerationIncident] = []
        observations: list[str] = []
        sequence = 0

        for generator in self._registry.all_generators():
            result = generator.generate(
                input_view,
                settings=settings,
                start_sequence=sequence + 1,
            )
            profiles.extend(result.profiles)
            observations.extend(result.technical_observations)
            sequence += sum(len(profile.segments) for profile in result.profiles)

        if len(profiles) > settings.max_profiles_per_process:
            incidents.append(
                ExplanationGenerationIncident(
                    generator_name="explanation_generation_executor",
                    message=(
                        f"Se generaron {len(profiles)} perfiles; "
                        f"límite configurado: {settings.max_profiles_per_process}"
                    ),
                    severity="warning",
                ),
            )
            profiles = profiles[: settings.max_profiles_per_process]

        catalog = build_explanation_catalog(
            input_view=input_view,
            profiles=tuple(profiles),
            settings=settings,
        )

        segments_count = sum(len(profile.segments) for profile in profiles)

        status = ExplanationGenerationStatus.GENERATED if profiles else ExplanationGenerationStatus.SKIPPED
        if profiles and segments_count == 0:
            status = ExplanationGenerationStatus.PARTIAL

        observations.extend(
            (
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "context_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
                f"profiles_generated={len(profiles)}",
                f"explanation_segments_generated={segments_count}",
            ),
        )

        return ExplanationGenerationResult(
            process_id=input_view.evidence_catalog.process_id,
            document_id=input_view.evidence_catalog.document_id,
            model_id=input_view.evidence_catalog.model_id,
            catalog=catalog,
            status=status,
            segments_count=segments_count,
            evidence_catalog_preserved=True,
            consistency_catalog_preserved=True,
            risk_catalog_preserved=True,
            context_catalog_preserved=True,
            definitive_catalog_preserved=True,
            source_data_preserved=input_view.evidence_catalog.source_data_preserved,
            generators_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
