"""Gateway de consumo de entradas del EGE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogGateway,
    EvidenceAnalysisCatalogView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationCatalog,
    ModelConsistencyProfile,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.gateway import (
    RequirementContextView,
    _build_requirement_context_from_definitive,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationCatalog,
    ModelContextProfile,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogGateway,
    DefinitiveComparativeModelCatalogView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisCatalog,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.exceptions import (
    ExplanationInputAccessError,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.governance import (
    PM7_CONTEXT_CATALOG_REQUIRED_FIELDS,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    ModelRiskProfile,
    RiskAnalysisCatalog,
    RiskRecord,
)


@dataclass(frozen=True)
class ModelConsistencyProfileView:
    """Vista de solo lectura del perfil de consistencia."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    inconsistencies: tuple[Any, ...]
    sufficiency_level: str
    sufficient_for_reasoning: bool
    blocking_factors: tuple[str, ...]
    source_data_preserved: bool
    raw_profile: ModelConsistencyProfile


@dataclass(frozen=True)
class ConsistencyEvaluationCatalogView:
    """Vista de solo lectura del catálogo de consistencia."""

    catalog_id: str
    process_id: str
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    profiles: tuple[ModelConsistencyProfileView, ...]
    evidence_catalog_preserved: bool
    source_data_preserved: bool
    raw_catalog: ConsistencyEvaluationCatalog


@dataclass(frozen=True)
class ModelRiskProfileView:
    """Vista de solo lectura del perfil de riesgos."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    risks: tuple[RiskRecord, ...]
    source_data_preserved: bool
    raw_profile: ModelRiskProfile


@dataclass(frozen=True)
class RiskAnalysisCatalogView:
    """Vista de solo lectura del catálogo de riesgos."""

    catalog_id: str
    process_id: str
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    profiles: tuple[ModelRiskProfileView, ...]
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    source_data_preserved: bool
    raw_catalog: RiskAnalysisCatalog


@dataclass(frozen=True)
class ModelContextProfileView:
    """Vista de solo lectura del perfil contextual."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    associations: tuple[Any, ...]
    contextual_gaps: tuple[Any, ...]
    context_elements_evaluated: int
    source_data_preserved: bool
    raw_profile: ModelContextProfile


@dataclass(frozen=True)
class ContextEvaluationCatalogView:
    """Vista de solo lectura del catálogo contextual."""

    catalog_id: str
    process_id: str
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelContextProfileView, ...]
    explanation_generation_engine_prepared: bool
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    definitive_catalog_preserved: bool
    requirement_context_preserved: bool
    source_data_preserved: bool
    raw_catalog: ContextEvaluationCatalog


@dataclass(frozen=True)
class ExplanationGenerationInputView:
    """Vista combinada de solo lectura — EAE + CEE + RAE + CxEE + PM6."""

    evidence_catalog: EvidenceAnalysisCatalogView
    consistency_catalog: ConsistencyEvaluationCatalogView
    risk_catalog: RiskAnalysisCatalogView
    context_catalog: ContextEvaluationCatalogView
    definitive_catalog: DefinitiveComparativeModelCatalogView
    requirement_context: RequirementContextView


def _parse_consistency_profile(payload: ModelConsistencyProfile) -> ModelConsistencyProfileView:
    sufficiency = payload.sufficiency
    return ModelConsistencyProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        inconsistencies=payload.inconsistencies,
        sufficiency_level=sufficiency.sufficiency_level.value,
        sufficient_for_reasoning=sufficiency.sufficient_for_reasoning,
        blocking_factors=sufficiency.blocking_factors,
        source_data_preserved=payload.source_data_preserved,
        raw_profile=payload,
    )


def _parse_risk_profile(payload: ModelRiskProfile) -> ModelRiskProfileView:
    return ModelRiskProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        risks=payload.risks,
        source_data_preserved=payload.source_data_preserved,
        raw_profile=payload,
    )


def _parse_context_profile(payload: ModelContextProfile) -> ModelContextProfileView:
    return ModelContextProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        associations=payload.associations,
        contextual_gaps=payload.contextual_gaps,
        context_elements_evaluated=payload.context_elements_evaluated,
        source_data_preserved=payload.source_data_preserved,
        raw_profile=payload,
    )


class ExplanationGenerationInputGateway:
    """
    Gateway de consumo de entradas del EGE.

    Valida el contrato EAE→CEE→RAE→CxEE→PM6 sin acceder a documentos originales.
    """

    EVIDENCE_GATEWAY = EvidenceAnalysisCatalogGateway()
    DEFINITIVE_GATEWAY = DefinitiveComparativeModelCatalogGateway()

    def validate(
        self,
        *,
        evidence_catalog: EvidenceAnalysisCatalog,
        consistency_catalog: ConsistencyEvaluationCatalog,
        risk_catalog: RiskAnalysisCatalog,
        context_catalog: ContextEvaluationCatalog,
        definitive_catalog: dict[str, Any],
    ) -> ExplanationGenerationInputView:
        if not isinstance(evidence_catalog, EvidenceAnalysisCatalog):
            raise ExplanationInputAccessError(
                "El catálogo de evidencias debe ser una instancia de EvidenceAnalysisCatalog",
            )
        if not isinstance(consistency_catalog, ConsistencyEvaluationCatalog):
            raise ExplanationInputAccessError(
                "El catálogo de consistencia debe ser una instancia de ConsistencyEvaluationCatalog",
            )
        if not isinstance(risk_catalog, RiskAnalysisCatalog):
            raise ExplanationInputAccessError(
                "El catálogo de riesgos debe ser una instancia de RiskAnalysisCatalog",
            )
        if not isinstance(context_catalog, ContextEvaluationCatalog):
            raise ExplanationInputAccessError(
                "El catálogo contextual debe ser una instancia de ContextEvaluationCatalog",
            )
        if not isinstance(definitive_catalog, dict):
            raise ExplanationInputAccessError(
                "El Modelo Comparativo Definitivo debe ser un diccionario",
            )

        evidence_view = self.EVIDENCE_GATEWAY.validate(evidence_catalog)
        definitive_view = self.DEFINITIVE_GATEWAY.validate(definitive_catalog)

        context_dict = context_catalog.to_dict()
        missing_context = [
            field for field in PM7_CONTEXT_CATALOG_REQUIRED_FIELDS if field not in context_dict
        ]
        if missing_context:
            raise ExplanationInputAccessError(
                "Campos obligatorios ausentes en catálogo contextual: " + ", ".join(missing_context),
            )

        if not bool(context_catalog.explanation_generation_engine_prepared):
            raise ExplanationInputAccessError(
                "El catálogo contextual no está preparado para generación de explicaciones",
            )

        process_ids = {
            str(evidence_catalog.process_id),
            str(consistency_catalog.process_id),
            str(risk_catalog.process_id),
            str(context_catalog.process_id),
            str(definitive_view.process_id),
        }
        if len(process_ids) > 1:
            raise ExplanationInputAccessError("process_id inconsistente entre entradas del EGE")

        if evidence_catalog.catalog_id != consistency_catalog.source_evidence_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo de consistencia no referencia al catálogo de evidencias de origen",
            )
        if evidence_catalog.catalog_id != risk_catalog.source_evidence_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo de riesgos no referencia al catálogo de evidencias de origen",
            )
        if consistency_catalog.catalog_id != risk_catalog.source_consistency_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo de riesgos no referencia al catálogo de consistencia de origen",
            )
        if evidence_catalog.catalog_id != context_catalog.source_evidence_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo contextual no referencia al catálogo de evidencias de origen",
            )
        if consistency_catalog.catalog_id != context_catalog.source_consistency_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo contextual no referencia al catálogo de consistencia de origen",
            )
        if risk_catalog.catalog_id != context_catalog.source_risk_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo contextual no referencia al catálogo de riesgos de origen",
            )
        if definitive_view.catalog_id != evidence_catalog.source_definitive_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo de evidencias no referencia al Modelo Comparativo Definitivo de origen",
            )
        if definitive_view.catalog_id != context_catalog.source_definitive_catalog_id:
            raise ExplanationInputAccessError(
                "El catálogo contextual no referencia al Modelo Comparativo Definitivo de origen",
            )

        consistency_profiles = tuple(
            _parse_consistency_profile(profile) for profile in consistency_catalog.profiles
        )
        risk_profiles = tuple(_parse_risk_profile(profile) for profile in risk_catalog.profiles)
        context_profiles = tuple(
            _parse_context_profile(profile) for profile in context_catalog.profiles
        )

        requirement_context = self._resolve_requirement_context(definitive_view)

        return ExplanationGenerationInputView(
            evidence_catalog=evidence_view,
            consistency_catalog=ConsistencyEvaluationCatalogView(
                catalog_id=consistency_catalog.catalog_id,
                process_id=str(consistency_catalog.process_id),
                model_id=consistency_catalog.model_id,
                document_id=consistency_catalog.document_id,
                source_evidence_catalog_id=consistency_catalog.source_evidence_catalog_id,
                profiles=consistency_profiles,
                evidence_catalog_preserved=True,
                source_data_preserved=True,
                raw_catalog=consistency_catalog,
            ),
            risk_catalog=RiskAnalysisCatalogView(
                catalog_id=risk_catalog.catalog_id,
                process_id=str(risk_catalog.process_id),
                model_id=risk_catalog.model_id,
                document_id=risk_catalog.document_id,
                source_evidence_catalog_id=risk_catalog.source_evidence_catalog_id,
                source_consistency_catalog_id=risk_catalog.source_consistency_catalog_id,
                profiles=risk_profiles,
                evidence_catalog_preserved=True,
                consistency_catalog_preserved=True,
                source_data_preserved=True,
                raw_catalog=risk_catalog,
            ),
            context_catalog=ContextEvaluationCatalogView(
                catalog_id=context_catalog.catalog_id,
                process_id=str(context_catalog.process_id),
                model_id=context_catalog.model_id,
                document_id=context_catalog.document_id,
                source_evidence_catalog_id=context_catalog.source_evidence_catalog_id,
                source_consistency_catalog_id=context_catalog.source_consistency_catalog_id,
                source_risk_catalog_id=context_catalog.source_risk_catalog_id,
                source_definitive_catalog_id=context_catalog.source_definitive_catalog_id,
                profiles=context_profiles,
                explanation_generation_engine_prepared=True,
                evidence_catalog_preserved=True,
                consistency_catalog_preserved=True,
                risk_catalog_preserved=True,
                definitive_catalog_preserved=True,
                requirement_context_preserved=True,
                source_data_preserved=True,
                raw_catalog=context_catalog,
            ),
            definitive_catalog=definitive_view,
            requirement_context=requirement_context,
        )

    def _resolve_requirement_context(
        self,
        definitive_view: DefinitiveComparativeModelCatalogView,
    ) -> RequirementContextView:
        return _build_requirement_context_from_definitive(definitive_view, {})

    def snapshot(self) -> dict[str, object]:
        return {
            "access_mode": "read_only",
            "modifies_evidence_catalog": False,
            "modifies_consistency_catalog": False,
            "modifies_risk_catalog": False,
            "modifies_context_catalog": False,
            "modifies_definitive_catalog": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "evidence_gateway": self.EVIDENCE_GATEWAY.snapshot(),
            "definitive_gateway": self.DEFINITIVE_GATEWAY.snapshot(),
        }
