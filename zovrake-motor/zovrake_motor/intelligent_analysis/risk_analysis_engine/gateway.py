"""Gateway de consumo de salidas del EAE y CEE para el RAE."""

from __future__ import annotations

from dataclasses import dataclass

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogGateway,
    EvidenceAnalysisCatalogView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationCatalog,
    InconsistencyRecord,
    ModelConsistencyProfile,
    SufficiencyAssessment,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisCatalog,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.exceptions import (
    AnalysisInputAccessError,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.governance import (
    PM7_CONSISTENCY_CATALOG_REQUIRED_FIELDS,
)


@dataclass(frozen=True)
class ModelConsistencyProfileView:
    """Vista de solo lectura del perfil de consistencia."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    inconsistencies: tuple[InconsistencyRecord, ...]
    sufficiency: SufficiencyAssessment
    criteria_evaluated: tuple[str, ...]
    evidence_records_evaluated: int
    source_data_preserved: bool


@dataclass(frozen=True)
class ConsistencyEvaluationCatalogView:
    """Vista de solo lectura del catálogo de consistencia del CEE."""

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
class EvidenceAndConsistencyInputView:
    """Vista combinada de solo lectura — EAE + CEE."""

    evidence_catalog: EvidenceAnalysisCatalogView
    consistency_catalog: ConsistencyEvaluationCatalogView


def _parse_consistency_profile(payload: ModelConsistencyProfile) -> ModelConsistencyProfileView:
    return ModelConsistencyProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        inconsistencies=payload.inconsistencies,
        sufficiency=payload.sufficiency,
        criteria_evaluated=payload.criteria_evaluated,
        evidence_records_evaluated=payload.evidence_records_evaluated,
        source_data_preserved=payload.source_data_preserved,
    )


class EvidenceAndConsistencyInputGateway:
    """
    Gateway de consumo de salidas del EAE y CEE.

    Valida el contrato EAE→CEE→RAE sin acceder al Modelo Comparativo Definitivo.
    """

    EVIDENCE_GATEWAY = EvidenceAnalysisCatalogGateway()
    CONSISTENCY_REQUIRED_FIELDS: tuple[str, ...] = PM7_CONSISTENCY_CATALOG_REQUIRED_FIELDS

    def validate(
        self,
        *,
        evidence_catalog: EvidenceAnalysisCatalog,
        consistency_catalog: ConsistencyEvaluationCatalog,
    ) -> EvidenceAndConsistencyInputView:
        if not isinstance(evidence_catalog, EvidenceAnalysisCatalog):
            raise AnalysisInputAccessError(
                "El catálogo de evidencias debe ser una instancia de EvidenceAnalysisCatalog",
            )
        if not isinstance(consistency_catalog, ConsistencyEvaluationCatalog):
            raise AnalysisInputAccessError(
                "El catálogo de consistencia debe ser una instancia de ConsistencyEvaluationCatalog",
            )

        evidence_view = self.EVIDENCE_GATEWAY.validate(evidence_catalog)

        consistency_dict = consistency_catalog.to_dict()
        missing = [
            field
            for field in self.CONSISTENCY_REQUIRED_FIELDS
            if field not in consistency_dict
        ]
        if missing:
            raise AnalysisInputAccessError(
                "Campos obligatorios ausentes en catálogo de consistencia: " + ", ".join(missing),
            )

        if not bool(consistency_catalog.risk_analysis_engine_prepared):
            raise AnalysisInputAccessError(
                "El catálogo de consistencia no está preparado para análisis de riesgos",
            )

        if not bool(consistency_catalog.evidence_catalog_preserved):
            raise AnalysisInputAccessError(
                "El catálogo de consistencia no preserva el catálogo de evidencias",
            )

        if not bool(consistency_catalog.source_data_preserved):
            raise AnalysisInputAccessError(
                "El catálogo de consistencia no preserva los datos de origen",
            )

        if str(evidence_catalog.process_id) != str(consistency_catalog.process_id):
            raise AnalysisInputAccessError(
                "process_id inconsistente entre catálogos de evidencias y consistencia",
            )

        if evidence_catalog.catalog_id != consistency_catalog.source_evidence_catalog_id:
            raise AnalysisInputAccessError(
                "El catálogo de consistencia no referencia al catálogo de evidencias de origen",
            )

        consistency_profiles = tuple(
            _parse_consistency_profile(profile) for profile in consistency_catalog.profiles
        )

        consistency_view = ConsistencyEvaluationCatalogView(
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
        )

        return EvidenceAndConsistencyInputView(
            evidence_catalog=evidence_view,
            consistency_catalog=consistency_view,
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "access_mode": "read_only",
            "modifies_evidence_catalog": False,
            "modifies_consistency_catalog": False,
            "accesses_definitive_model": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "evidence_gateway": self.EVIDENCE_GATEWAY.snapshot(),
            "consistency_required_fields": list(self.CONSISTENCY_REQUIRED_FIELDS),
        }
