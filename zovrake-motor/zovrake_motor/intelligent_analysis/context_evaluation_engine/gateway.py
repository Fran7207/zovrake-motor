"""Gateway de consumo de entradas del CxEE."""

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
from zovrake_motor.intelligent_analysis.context_evaluation_engine.exceptions import (
    ContextInputAccessError,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.governance import (
    PM7_REQUIREMENT_CONTEXT_REQUIRED_FIELDS,
    PM7_RISK_CATALOG_REQUIRED_FIELDS,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogGateway,
    DefinitiveComparativeModelCatalogView,
    DefinitiveComparativeModelView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisCatalog,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    ModelRiskProfile,
    RiskAnalysisCatalog,
    RiskRecord,
)


@dataclass(frozen=True)
class RequirementContextView:
    """Vista de solo lectura del contexto del requerimiento (PM4)."""

    context_id: str
    codigo_req: str
    description: str
    commercial_requirements: dict[str, Any]
    technical_requirements: dict[str, Any]
    metadata: dict[str, Any]
    raw_context: dict[str, Any]


@dataclass(frozen=True)
class ModelConsistencyProfileView:
    """Vista de solo lectura del perfil de consistencia."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
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
    risk_analysis_engine_prepared: bool
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
    """Vista de solo lectura del catálogo de riesgos del RAE."""

    catalog_id: str
    process_id: str
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    profiles: tuple[ModelRiskProfileView, ...]
    context_evaluation_engine_prepared: bool
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    source_data_preserved: bool
    raw_catalog: RiskAnalysisCatalog


@dataclass(frozen=True)
class ContextEvaluationInputView:
    """Vista combinada de solo lectura — EAE + CEE + RAE + PM6 + PM4."""

    evidence_catalog: EvidenceAnalysisCatalogView
    consistency_catalog: ConsistencyEvaluationCatalogView
    risk_catalog: RiskAnalysisCatalogView
    definitive_catalog: DefinitiveComparativeModelCatalogView
    requirement_context: RequirementContextView


def _parse_requirement_context(context_dict: dict[str, Any]) -> RequirementContextView:
    missing = [field for field in PM7_REQUIREMENT_CONTEXT_REQUIRED_FIELDS if field not in context_dict]
    if missing and not context_dict.get("description") and not context_dict.get("detalles_requerimiento"):
        if missing:
            raise ContextInputAccessError(
                "Campos obligatorios ausentes en contexto del requerimiento: " + ", ".join(missing),
            )

    description = str(
        context_dict.get("description")
        or context_dict.get("detalles_requerimiento")
        or "",
    )
    commercial = dict(context_dict.get("commercial_requirements", {}))
    technical = dict(context_dict.get("technical_requirements", {}))

    if not commercial and isinstance(context_dict.get("commercial_fields"), dict):
        commercial = dict(context_dict["commercial_fields"])
    if not technical and isinstance(context_dict.get("technical_fields"), dict):
        technical = dict(context_dict["technical_fields"])

    return RequirementContextView(
        context_id=str(context_dict.get("context_id", context_dict.get("related_context_id", ""))),
        codigo_req=str(context_dict.get("codigo_req", "")),
        description=description,
        commercial_requirements=commercial,
        technical_requirements=technical,
        metadata=dict(context_dict.get("metadata", {})),
        raw_context=dict(context_dict),
    )


def _build_requirement_context_from_definitive(
    definitive_view: DefinitiveComparativeModelCatalogView,
    explicit_context: dict[str, Any],
) -> RequirementContextView:
    if explicit_context:
        return _parse_requirement_context(explicit_context)

    inherited: dict[str, Any] = {}
    if definitive_view.models:
        inherited = dict(definitive_view.models[0].inherited_context)

    if inherited:
        return _parse_requirement_context(inherited)

    return RequirementContextView(
        context_id="",
        codigo_req="",
        description="",
        commercial_requirements={},
        technical_requirements={},
        metadata={},
        raw_context={},
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


def _parse_consistency_profile(payload: ModelConsistencyProfile) -> ModelConsistencyProfileView:
    return ModelConsistencyProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        source_data_preserved=payload.source_data_preserved,
        raw_profile=payload,
    )


class ContextEvaluationInputGateway:
    """
    Gateway de consumo de entradas del CxEE.

    Valida el contrato EAE→CEE→RAE→PM6→PM4 sin acceder a documentos originales.
    """

    EVIDENCE_GATEWAY = EvidenceAnalysisCatalogGateway()
    DEFINITIVE_GATEWAY = DefinitiveComparativeModelCatalogGateway()

    def validate(
        self,
        *,
        evidence_catalog: EvidenceAnalysisCatalog,
        consistency_catalog: ConsistencyEvaluationCatalog,
        risk_catalog: RiskAnalysisCatalog,
        definitive_catalog: dict[str, Any],
        requirement_context: dict[str, Any] | None = None,
    ) -> ContextEvaluationInputView:
        if not isinstance(evidence_catalog, EvidenceAnalysisCatalog):
            raise ContextInputAccessError(
                "El catálogo de evidencias debe ser una instancia de EvidenceAnalysisCatalog",
            )
        if not isinstance(consistency_catalog, ConsistencyEvaluationCatalog):
            raise ContextInputAccessError(
                "El catálogo de consistencia debe ser una instancia de ConsistencyEvaluationCatalog",
            )
        if not isinstance(risk_catalog, RiskAnalysisCatalog):
            raise ContextInputAccessError(
                "El catálogo de riesgos debe ser una instancia de RiskAnalysisCatalog",
            )
        if not isinstance(definitive_catalog, dict):
            raise ContextInputAccessError(
                "El Modelo Comparativo Definitivo debe ser un diccionario",
            )

        evidence_view = self.EVIDENCE_GATEWAY.validate(evidence_catalog)
        definitive_view = self.DEFINITIVE_GATEWAY.validate(definitive_catalog)

        consistency_dict = consistency_catalog.to_dict()
        missing_consistency = [
            field
            for field in (
                "catalog_id",
                "process_id",
                "model_id",
                "document_id",
                "source_evidence_catalog_id",
                "profiles",
                "risk_analysis_engine_prepared",
                "evidence_catalog_preserved",
                "source_data_preserved",
            )
            if field not in consistency_dict
        ]
        if missing_consistency:
            raise ContextInputAccessError(
                "Campos obligatorios ausentes en catálogo de consistencia: "
                + ", ".join(missing_consistency),
            )

        risk_dict = risk_catalog.to_dict()
        missing_risk = [field for field in PM7_RISK_CATALOG_REQUIRED_FIELDS if field not in risk_dict]
        if missing_risk:
            raise ContextInputAccessError(
                "Campos obligatorios ausentes en catálogo de riesgos: " + ", ".join(missing_risk),
            )

        if not bool(risk_catalog.context_evaluation_engine_prepared):
            raise ContextInputAccessError(
                "El catálogo de riesgos no está preparado para evaluación contextual",
            )

        process_ids = {
            str(evidence_catalog.process_id),
            str(consistency_catalog.process_id),
            str(risk_catalog.process_id),
            str(definitive_view.process_id),
        }
        if len(process_ids) > 1:
            raise ContextInputAccessError("process_id inconsistente entre entradas del CxEE")

        if evidence_catalog.catalog_id != consistency_catalog.source_evidence_catalog_id:
            raise ContextInputAccessError(
                "El catálogo de consistencia no referencia al catálogo de evidencias de origen",
            )
        if evidence_catalog.catalog_id != risk_catalog.source_evidence_catalog_id:
            raise ContextInputAccessError(
                "El catálogo de riesgos no referencia al catálogo de evidencias de origen",
            )
        if consistency_catalog.catalog_id != risk_catalog.source_consistency_catalog_id:
            raise ContextInputAccessError(
                "El catálogo de riesgos no referencia al catálogo de consistencia de origen",
            )
        if definitive_view.catalog_id != evidence_catalog.source_definitive_catalog_id:
            raise ContextInputAccessError(
                "El catálogo de evidencias no referencia al Modelo Comparativo Definitivo de origen",
            )

        consistency_profiles = tuple(
            _parse_consistency_profile(profile) for profile in consistency_catalog.profiles
        )
        risk_profiles = tuple(_parse_risk_profile(profile) for profile in risk_catalog.profiles)

        requirement_view = _build_requirement_context_from_definitive(
            definitive_view,
            dict(requirement_context or {}),
        )

        return ContextEvaluationInputView(
            evidence_catalog=evidence_view,
            consistency_catalog=ConsistencyEvaluationCatalogView(
                catalog_id=consistency_catalog.catalog_id,
                process_id=str(consistency_catalog.process_id),
                model_id=consistency_catalog.model_id,
                document_id=consistency_catalog.document_id,
                source_evidence_catalog_id=consistency_catalog.source_evidence_catalog_id,
                profiles=consistency_profiles,
                risk_analysis_engine_prepared=True,
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
                context_evaluation_engine_prepared=True,
                evidence_catalog_preserved=True,
                consistency_catalog_preserved=True,
                source_data_preserved=True,
                raw_catalog=risk_catalog,
            ),
            definitive_catalog=definitive_view,
            requirement_context=requirement_view,
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "access_mode": "read_only",
            "modifies_evidence_catalog": False,
            "modifies_consistency_catalog": False,
            "modifies_risk_catalog": False,
            "modifies_definitive_catalog": False,
            "modifies_requirement_context": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "evidence_gateway": self.EVIDENCE_GATEWAY.snapshot(),
            "definitive_gateway": self.DEFINITIVE_GATEWAY.snapshot(),
        }
