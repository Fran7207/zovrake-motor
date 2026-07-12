"""Gateway de consumo de entradas del RRB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    RecommendationGenerationInputGateway,
    RecommendationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    ModelRecommendationProfile,
    RecommendationGenerationCatalog,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.exceptions import (
    ReasoningResultInputAccessError,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.governance import (
    PM7_RECOMMENDATION_CATALOG_REQUIRED_FIELDS,
)


@dataclass(frozen=True)
class ModelRecommendationProfileView:
    """Vista de solo lectura del perfil de recomendación."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    scenario_type: str
    confidence_level: str
    recommended_provider_id: str | None
    primary_strengths: tuple[str, ...]
    identified_risks: tuple[str, ...]
    limitations: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    source_data_preserved: bool
    raw_profile: ModelRecommendationProfile


@dataclass(frozen=True)
class RecommendationGenerationCatalogView:
    """Vista de solo lectura del catálogo de recomendaciones."""

    catalog_id: str
    process_id: str
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_context_catalog_id: str
    source_explanation_catalog_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelRecommendationProfileView, ...]
    reasoning_result_builder_prepared: bool
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    context_catalog_preserved: bool
    explanation_catalog_preserved: bool
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    raw_catalog: RecommendationGenerationCatalog


@dataclass(frozen=True)
class ReasoningResultInputView:
    """Vista combinada de solo lectura — EAE + CEE + RAE + CxEE + EGE + RGE + PM6."""

    evidence_catalog: Any
    consistency_catalog: Any
    risk_catalog: Any
    context_catalog: Any
    explanation_catalog: Any
    recommendation_catalog: RecommendationGenerationCatalogView
    definitive_catalog: Any
    requirement_context: Any


def _parse_recommendation_profile(payload: ModelRecommendationProfile) -> ModelRecommendationProfileView:
    return ModelRecommendationProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        scenario_type=payload.scenario_type.value,
        confidence_level=payload.confidence_level.value,
        recommended_provider_id=payload.recommended_provider_id,
        primary_strengths=payload.primary_strengths,
        identified_risks=payload.identified_risks,
        limitations=payload.limitations,
        supporting_evidence_ids=payload.supporting_evidence_ids,
        source_data_preserved=payload.source_data_preserved,
        raw_profile=payload,
    )


class ReasoningResultInputGateway:
    """
    Gateway de consumo de entradas del RRB.

    Valida el contrato EAE→CEE→RAE→CxEE→EGE→RGE→PM6 sin acceder a documentos originales.
    """

    RECOMMENDATION_INPUT_GATEWAY = RecommendationGenerationInputGateway()

    def validate(
        self,
        *,
        evidence_catalog: Any,
        consistency_catalog: Any,
        risk_catalog: Any,
        context_catalog: Any,
        explanation_catalog: Any,
        recommendation_catalog: RecommendationGenerationCatalog,
        definitive_catalog: dict[str, Any],
    ) -> ReasoningResultInputView:
        if not isinstance(recommendation_catalog, RecommendationGenerationCatalog):
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones debe ser una instancia de RecommendationGenerationCatalog",
            )

        base_view = self.RECOMMENDATION_INPUT_GATEWAY.validate(
            evidence_catalog=evidence_catalog,
            consistency_catalog=consistency_catalog,
            risk_catalog=risk_catalog,
            context_catalog=context_catalog,
            explanation_catalog=explanation_catalog,
            definitive_catalog=definitive_catalog,
        )

        recommendation_dict = recommendation_catalog.to_dict()
        missing_recommendation = [
            field
            for field in PM7_RECOMMENDATION_CATALOG_REQUIRED_FIELDS
            if field not in recommendation_dict
        ]
        if missing_recommendation:
            raise ReasoningResultInputAccessError(
                "Campos obligatorios ausentes en catálogo de recomendaciones: "
                + ", ".join(missing_recommendation),
            )

        if not bool(recommendation_catalog.reasoning_result_builder_prepared):
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no está preparado para construcción de resultados",
            )

        if str(recommendation_catalog.process_id) != str(base_view.evidence_catalog.process_id):
            raise ReasoningResultInputAccessError("process_id inconsistente en catálogo de recomendaciones")

        if recommendation_catalog.source_evidence_catalog_id != base_view.evidence_catalog.catalog_id:
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no referencia al catálogo de evidencias de origen",
            )
        if recommendation_catalog.source_consistency_catalog_id != base_view.consistency_catalog.catalog_id:
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no referencia al catálogo de consistencia de origen",
            )
        if recommendation_catalog.source_risk_catalog_id != base_view.risk_catalog.catalog_id:
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no referencia al catálogo de riesgos de origen",
            )
        if recommendation_catalog.source_context_catalog_id != base_view.context_catalog.catalog_id:
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no referencia al catálogo contextual de origen",
            )
        if recommendation_catalog.source_explanation_catalog_id != base_view.explanation_catalog.catalog_id:
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no referencia al catálogo de explicaciones de origen",
            )
        if recommendation_catalog.source_definitive_catalog_id != base_view.definitive_catalog.catalog_id:
            raise ReasoningResultInputAccessError(
                "El catálogo de recomendaciones no referencia al Modelo Comparativo Definitivo de origen",
            )

        recommendation_profiles = tuple(
            _parse_recommendation_profile(profile) for profile in recommendation_catalog.profiles
        )

        return ReasoningResultInputView(
            evidence_catalog=base_view.evidence_catalog,
            consistency_catalog=base_view.consistency_catalog,
            risk_catalog=base_view.risk_catalog,
            context_catalog=base_view.context_catalog,
            explanation_catalog=base_view.explanation_catalog,
            recommendation_catalog=RecommendationGenerationCatalogView(
                catalog_id=recommendation_catalog.catalog_id,
                process_id=str(recommendation_catalog.process_id),
                model_id=recommendation_catalog.model_id,
                document_id=recommendation_catalog.document_id,
                source_evidence_catalog_id=recommendation_catalog.source_evidence_catalog_id,
                source_consistency_catalog_id=recommendation_catalog.source_consistency_catalog_id,
                source_risk_catalog_id=recommendation_catalog.source_risk_catalog_id,
                source_context_catalog_id=recommendation_catalog.source_context_catalog_id,
                source_explanation_catalog_id=recommendation_catalog.source_explanation_catalog_id,
                source_definitive_catalog_id=recommendation_catalog.source_definitive_catalog_id,
                profiles=recommendation_profiles,
                reasoning_result_builder_prepared=True,
                evidence_catalog_preserved=True,
                consistency_catalog_preserved=True,
                risk_catalog_preserved=True,
                context_catalog_preserved=True,
                explanation_catalog_preserved=True,
                definitive_catalog_preserved=True,
                source_data_preserved=True,
                raw_catalog=recommendation_catalog,
            ),
            definitive_catalog=base_view.definitive_catalog,
            requirement_context=base_view.requirement_context,
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "access_mode": "read_only",
            "modifies_upstream_catalogs": False,
            "modifies_definitive_catalog": False,
            "accesses_source_files": False,
            "recommendation_input_gateway": self.RECOMMENDATION_INPUT_GATEWAY.snapshot(),
        }
