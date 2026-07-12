"""Ejecutor de constructores del Reasoning Result Builder."""

from __future__ import annotations

from zovrake_motor.intelligent_analysis.reasoning_result_builder.builders import (
    build_intelligent_analysis_result_catalog,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.enums import ReasoningResultBuildStatus
from zovrake_motor.intelligent_analysis.reasoning_result_builder.gateway import ReasoningResultInputView
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    GroupIntelligentAnalysisResult,
    ReasoningResultBuildIncident,
    ReasoningResultBuildResult,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.registry import (
    ReasoningResultBuilderRegistry,
)
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings


class ReasoningResultBuildExecutor:
    """Coordina la ejecución secuencial de constructores sin modificar las entradas."""

    def __init__(self, registry: ReasoningResultBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ReasoningResultInputView,
        *,
        settings: ReasoningResultBuilderSettings,
    ) -> ReasoningResultBuildResult:
        results: list[GroupIntelligentAnalysisResult] = []
        incidents: list[ReasoningResultBuildIncident] = []
        observations: list[str] = []
        sequence = 0

        for builder in self._registry.all_builders():
            build_result = builder.build(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            results.extend(build_result.results)
            observations.extend(build_result.technical_observations)
            sequence += len(build_result.results)

        if len(results) > settings.max_results_per_process:
            incidents.append(
                ReasoningResultBuildIncident(
                    builder_name="reasoning_result_build_executor",
                    message=(
                        f"Se construyeron {len(results)} resultados; "
                        f"límite configurado: {settings.max_results_per_process}"
                    ),
                    severity="warning",
                ),
            )
            results = results[: settings.max_results_per_process]

        catalog = build_intelligent_analysis_result_catalog(
            input_view=input_view,
            results=tuple(results),
            settings=settings,
        )

        status = ReasoningResultBuildStatus.BUILT if results else ReasoningResultBuildStatus.SKIPPED

        observations.extend(
            (
                "evidence_catalog_preserved=True",
                "consistency_catalog_preserved=True",
                "risk_catalog_preserved=True",
                "context_catalog_preserved=True",
                "explanation_catalog_preserved=True",
                "recommendation_catalog_preserved=True",
                "definitive_catalog_preserved=True",
                "source_files_unaccessed=True",
                f"results_built={len(results)}",
            ),
        )

        return ReasoningResultBuildResult(
            process_id=input_view.evidence_catalog.process_id,
            document_id=input_view.evidence_catalog.document_id,
            model_id=input_view.evidence_catalog.model_id,
            catalog=catalog,
            status=status,
            results_count=len(results),
            evidence_catalog_preserved=True,
            consistency_catalog_preserved=True,
            risk_catalog_preserved=True,
            context_catalog_preserved=True,
            explanation_catalog_preserved=True,
            recommendation_catalog_preserved=True,
            definitive_catalog_preserved=True,
            source_data_preserved=input_view.evidence_catalog.source_data_preserved,
            builders_executed=self._registry.count(),
            incidents=tuple(incidents),
            technical_observations=tuple(observations),
        )
