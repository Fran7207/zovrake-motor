"""Gateway de consumo de entradas del RGE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ExplanationGenerationInputGateway,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationCatalog,
    ModelExplanationProfile,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.exceptions import (
    RecommendationInputAccessError,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.governance import (
    PM7_EXPLANATION_CATALOG_REQUIRED_FIELDS,
)


@dataclass(frozen=True)
class ModelExplanationProfileView:
    """Vista de solo lectura del perfil de explicación."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    segments: tuple[Any, ...]
    strengths_count: int
    weaknesses_count: int
    risks_count: int
    source_data_preserved: bool
    raw_profile: ModelExplanationProfile


@dataclass(frozen=True)
class ExplanationGenerationCatalogView:
    """Vista de solo lectura del catálogo de explicaciones."""

    catalog_id: str
    process_id: str
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_context_catalog_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelExplanationProfileView, ...]
    recommendation_generation_engine_prepared: bool
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    context_catalog_preserved: bool
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    raw_catalog: ExplanationGenerationCatalog


@dataclass(frozen=True)
class RecommendationGenerationInputView:
    """Vista combinada de solo lectura — EAE + CEE + RAE + CxEE + EGE + PM6."""

    evidence_catalog: Any
    consistency_catalog: Any
    risk_catalog: Any
    context_catalog: Any
    explanation_catalog: ExplanationGenerationCatalogView
    definitive_catalog: Any
    requirement_context: Any


def _parse_explanation_profile(payload: ModelExplanationProfile) -> ModelExplanationProfileView:
    return ModelExplanationProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        segments=payload.segments,
        strengths_count=payload.strengths_count,
        weaknesses_count=payload.weaknesses_count,
        risks_count=payload.risks_count,
        source_data_preserved=payload.source_data_preserved,
        raw_profile=payload,
    )


class RecommendationGenerationInputGateway:
    """
    Gateway de consumo de entradas del RGE.

    Valida el contrato EAE→CEE→RAE→CxEE→EGE→PM6 sin acceder a documentos originales.
    """

    EXPLANATION_INPUT_GATEWAY = ExplanationGenerationInputGateway()

    def validate(
        self,
        *,
        evidence_catalog: Any,
        consistency_catalog: Any,
        risk_catalog: Any,
        context_catalog: Any,
        explanation_catalog: ExplanationGenerationCatalog,
        definitive_catalog: dict[str, Any],
    ) -> RecommendationGenerationInputView:
        if not isinstance(explanation_catalog, ExplanationGenerationCatalog):
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones debe ser una instancia de ExplanationGenerationCatalog",
            )

        base_view = self.EXPLANATION_INPUT_GATEWAY.validate(
            evidence_catalog=evidence_catalog,
            consistency_catalog=consistency_catalog,
            risk_catalog=risk_catalog,
            context_catalog=context_catalog,
            definitive_catalog=definitive_catalog,
        )

        explanation_dict = explanation_catalog.to_dict()
        missing_explanation = [
            field
            for field in PM7_EXPLANATION_CATALOG_REQUIRED_FIELDS
            if field not in explanation_dict
        ]
        if missing_explanation:
            raise RecommendationInputAccessError(
                "Campos obligatorios ausentes en catálogo de explicaciones: "
                + ", ".join(missing_explanation),
            )

        if not bool(explanation_catalog.recommendation_generation_engine_prepared):
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones no está preparado para generación de recomendaciones",
            )

        if str(explanation_catalog.process_id) != str(base_view.evidence_catalog.process_id):
            raise RecommendationInputAccessError("process_id inconsistente en catálogo de explicaciones")

        if explanation_catalog.source_evidence_catalog_id != base_view.evidence_catalog.catalog_id:
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones no referencia al catálogo de evidencias de origen",
            )
        if explanation_catalog.source_consistency_catalog_id != base_view.consistency_catalog.catalog_id:
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones no referencia al catálogo de consistencia de origen",
            )
        if explanation_catalog.source_risk_catalog_id != base_view.risk_catalog.catalog_id:
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones no referencia al catálogo de riesgos de origen",
            )
        if explanation_catalog.source_context_catalog_id != base_view.context_catalog.catalog_id:
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones no referencia al catálogo contextual de origen",
            )
        if explanation_catalog.source_definitive_catalog_id != base_view.definitive_catalog.catalog_id:
            raise RecommendationInputAccessError(
                "El catálogo de explicaciones no referencia al Modelo Comparativo Definitivo de origen",
            )

        explanation_profiles = tuple(
            _parse_explanation_profile(profile) for profile in explanation_catalog.profiles
        )

        return RecommendationGenerationInputView(
            evidence_catalog=base_view.evidence_catalog,
            consistency_catalog=base_view.consistency_catalog,
            risk_catalog=base_view.risk_catalog,
            context_catalog=base_view.context_catalog,
            explanation_catalog=ExplanationGenerationCatalogView(
                catalog_id=explanation_catalog.catalog_id,
                process_id=str(explanation_catalog.process_id),
                model_id=explanation_catalog.model_id,
                document_id=explanation_catalog.document_id,
                source_evidence_catalog_id=explanation_catalog.source_evidence_catalog_id,
                source_consistency_catalog_id=explanation_catalog.source_consistency_catalog_id,
                source_risk_catalog_id=explanation_catalog.source_risk_catalog_id,
                source_context_catalog_id=explanation_catalog.source_context_catalog_id,
                source_definitive_catalog_id=explanation_catalog.source_definitive_catalog_id,
                profiles=explanation_profiles,
                recommendation_generation_engine_prepared=True,
                evidence_catalog_preserved=True,
                consistency_catalog_preserved=True,
                risk_catalog_preserved=True,
                context_catalog_preserved=True,
                definitive_catalog_preserved=True,
                source_data_preserved=True,
                raw_catalog=explanation_catalog,
            ),
            definitive_catalog=base_view.definitive_catalog,
            requirement_context=base_view.requirement_context,
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "access_mode": "read_only",
            "modifies_evidence_catalog": False,
            "modifies_consistency_catalog": False,
            "modifies_risk_catalog": False,
            "modifies_context_catalog": False,
            "modifies_explanation_catalog": False,
            "modifies_definitive_catalog": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "explanation_input_gateway": self.EXPLANATION_INPUT_GATEWAY.snapshot(),
        }
