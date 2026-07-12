"""Utilidades de identificación y clasificación de riesgos."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyCriterionType,
    InconsistencyType,
    SufficiencyLevel,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceRecordView,
    MissingEvidenceRecordView,
    ModelEvidenceProfileView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    InconsistencyRecord,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.enums import (
    RiskCategory,
    RiskStatus,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.gateway import (
    EvidenceAndConsistencyInputView,
    ModelConsistencyProfileView,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    ModelRiskProfile,
    RiskAnalysisCatalog,
    RiskRecord,
    RiskTraceabilityReference,
)
from zovrake_motor.config.categories.intelligent_analysis import RiskAnalysisEngineSettings


def build_public_risk_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def _build_risk_traceability_from_evidence(
    *,
    record: EvidenceRecordView,
    profile_view: ModelEvidenceProfileView,
    document_id: str,
) -> RiskTraceabilityReference:
    trace = record.traceability_ref
    return RiskTraceabilityReference(
        evidence_id=record.evidence_id,
        inconsistency_id=None,
        missing_evidence_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=record.provider_id,
        document_id=document_id,
        source_field=trace.source_field,
        traceability=dict(trace.traceability),
    )


def _build_risk_traceability_from_inconsistency(
    *,
    inconsistency: InconsistencyRecord,
    profile_view: ModelConsistencyProfileView,
    document_id: str,
) -> RiskTraceabilityReference:
    trace = inconsistency.traceability_ref
    return RiskTraceabilityReference(
        evidence_id=trace.evidence_id,
        inconsistency_id=inconsistency.inconsistency_id,
        missing_evidence_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=trace.provider_id,
        document_id=document_id,
        source_field=trace.source_field,
        traceability=dict(trace.traceability),
    )


def _build_risk_traceability_from_missing(
    *,
    missing: MissingEvidenceRecordView,
    profile_view: ModelEvidenceProfileView,
) -> RiskTraceabilityReference:
    return RiskTraceabilityReference(
        evidence_id=None,
        inconsistency_id=None,
        missing_evidence_id=missing.missing_evidence_id,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=missing.provider_id,
        document_id=missing.document_id,
        source_field=None,
        traceability={},
    )


def _append_risk(
    *,
    risks: list[RiskRecord],
    sequence: int,
    risk_category: RiskCategory,
    description: str,
    associated_evidence_ids: tuple[str, ...],
    associated_inconsistency_ids: tuple[str, ...],
    associated_missing_evidence_ids: tuple[str, ...],
    provider_ids: tuple[str, ...],
    traceability_ref: RiskTraceabilityReference,
    settings: RiskAnalysisEngineSettings,
    metadata: dict[str, Any] | None = None,
) -> int:
    sequence += 1
    risks.append(
        RiskRecord(
            risk_id=build_public_risk_id(
                sequence,
                prefix=settings.risk_id_prefix,
                padding=settings.risk_id_padding,
            ),
            risk_category=risk_category,
            description=description,
            associated_evidence_ids=associated_evidence_ids,
            associated_inconsistency_ids=associated_inconsistency_ids,
            associated_missing_evidence_ids=associated_missing_evidence_ids,
            provider_ids=provider_ids,
            traceability_ref=traceability_ref,
            risk_status=RiskStatus.IDENTIFIED,
            metadata=metadata or {},
        ),
    )
    return sequence


def _classify_inconsistency_risk(inconsistency: InconsistencyRecord) -> RiskCategory:
    if inconsistency.inconsistency_type == InconsistencyType.INCOMPLETE_REFERENCE:
        return RiskCategory.DOCUMENTATION
    if inconsistency.inconsistency_type == InconsistencyType.RELEVANT_DIFFERENCE:
        return RiskCategory.INFORMATION
    if inconsistency.inconsistency_type == InconsistencyType.INCONSISTENT_ATTRIBUTES:
        return RiskCategory.TECHNICAL
    if inconsistency.criterion == ConsistencyCriterionType.COMMERCIAL_TECHNICAL_COHERENCE:
        return RiskCategory.COMMERCIAL
    if inconsistency.criterion == ConsistencyCriterionType.PROVIDER_COMPARABILITY:
        return RiskCategory.INFORMATION
    if inconsistency.inconsistency_type == InconsistencyType.INCOMPATIBLE_DATA:
        if inconsistency.criterion in (
            ConsistencyCriterionType.COMMERCIAL_TECHNICAL_COHERENCE,
            ConsistencyCriterionType.PROVIDER_COMPARABILITY,
        ):
            return RiskCategory.COMMERCIAL
        return RiskCategory.TECHNICAL
    return RiskCategory.CONSISTENCY


def identify_missing_evidence_risks(
    *,
    input_view: EvidenceAndConsistencyInputView,
    evidence_profile: ModelEvidenceProfileView,
    risks: list[RiskRecord],
    sequence: int,
    settings: RiskAnalysisEngineSettings,
) -> int:
    if not settings.detect_documentation_risks and not settings.detect_information_risks:
        return sequence

    for missing in evidence_profile.missing_evidence_records:
        category = (
            RiskCategory.DOCUMENTATION
            if "categoría" in missing.reason.lower() or "celda" in missing.reason.lower()
            else RiskCategory.INFORMATION
        )
        if category == RiskCategory.DOCUMENTATION and not settings.detect_documentation_risks:
            continue
        if category == RiskCategory.INFORMATION and not settings.detect_information_risks:
            continue

        sequence = _append_risk(
            risks=risks,
            sequence=sequence,
            risk_category=category,
            description=f"Ausencia de evidencia: {missing.expected_key} — {missing.reason}",
            associated_evidence_ids=(),
            associated_inconsistency_ids=(),
            associated_missing_evidence_ids=(missing.missing_evidence_id,),
            provider_ids=(missing.provider_id,) if missing.provider_id else (),
            traceability_ref=_build_risk_traceability_from_missing(
                missing=missing,
                profile_view=evidence_profile,
            ),
            settings=settings,
            metadata={
                "expected_key": missing.expected_key,
                "evidence_category": missing.evidence_category.value,
            },
        )
    return sequence


def identify_inconsistency_risks(
    *,
    input_view: EvidenceAndConsistencyInputView,
    consistency_profile: ModelConsistencyProfileView,
    risks: list[RiskRecord],
    sequence: int,
    settings: RiskAnalysisEngineSettings,
) -> int:
    if not settings.detect_consistency_risks:
        return sequence

    for inconsistency in consistency_profile.inconsistencies:
        risk_category = _classify_inconsistency_risk(inconsistency)

        if risk_category == RiskCategory.COMMERCIAL and not settings.detect_commercial_risks:
            continue
        if risk_category == RiskCategory.TECHNICAL and not settings.detect_technical_risks:
            continue
        if risk_category == RiskCategory.DOCUMENTATION and not settings.detect_documentation_risks:
            continue
        if risk_category == RiskCategory.INFORMATION and not settings.detect_information_risks:
            continue
        if risk_category == RiskCategory.CONSISTENCY and not settings.detect_consistency_risks:
            continue

        sequence = _append_risk(
            risks=risks,
            sequence=sequence,
            risk_category=risk_category,
            description=inconsistency.description,
            associated_evidence_ids=inconsistency.related_evidence_ids,
            associated_inconsistency_ids=(inconsistency.inconsistency_id,),
            associated_missing_evidence_ids=(),
            provider_ids=inconsistency.provider_ids,
            traceability_ref=_build_risk_traceability_from_inconsistency(
                inconsistency=inconsistency,
                profile_view=consistency_profile,
                document_id=input_view.evidence_catalog.document_id,
            ),
            settings=settings,
            metadata={
                "inconsistency_type": inconsistency.inconsistency_type.value,
                "criterion": inconsistency.criterion.value,
            },
        )
    return sequence


def identify_sufficiency_risks(
    *,
    input_view: EvidenceAndConsistencyInputView,
    consistency_profile: ModelConsistencyProfileView,
    risks: list[RiskRecord],
    sequence: int,
    settings: RiskAnalysisEngineSettings,
) -> int:
    if not settings.detect_information_risks:
        return sequence

    sufficiency = consistency_profile.sufficiency
    if sufficiency.sufficiency_level == SufficiencyLevel.SUFFICIENT:
        return sequence

    sequence = _append_risk(
        risks=risks,
        sequence=sequence,
        risk_category=RiskCategory.INFORMATION,
        description=sufficiency.reason,
        associated_evidence_ids=(),
        associated_inconsistency_ids=(),
        associated_missing_evidence_ids=(),
        provider_ids=(),
        traceability_ref=RiskTraceabilityReference(
            evidence_id=None,
            inconsistency_id=None,
            missing_evidence_id=None,
            definitive_model_id=consistency_profile.definitive_model_id,
            group_id=consistency_profile.group_id,
            comparative_table_id=consistency_profile.comparative_table_id,
            provider_id=None,
            document_id=input_view.evidence_catalog.document_id,
            source_field=None,
            traceability={
                "sufficiency_level": sufficiency.sufficiency_level.value,
                "blocking_factors": list(sufficiency.blocking_factors),
            },
        ),
        settings=settings,
        metadata={
            "sufficiency_level": sufficiency.sufficiency_level.value,
            "blocking_factors": list(sufficiency.blocking_factors),
        },
    )
    return sequence


def identify_profile_risks(
    *,
    input_view: EvidenceAndConsistencyInputView,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView,
    settings: RiskAnalysisEngineSettings,
    start_sequence: int,
) -> tuple[ModelRiskProfile, int]:
    risks: list[RiskRecord] = []
    sequence = start_sequence

    sequence = identify_missing_evidence_risks(
        input_view=input_view,
        evidence_profile=evidence_profile,
        risks=risks,
        sequence=sequence,
        settings=settings,
    )
    sequence = identify_inconsistency_risks(
        input_view=input_view,
        consistency_profile=consistency_profile,
        risks=risks,
        sequence=sequence,
        settings=settings,
    )
    sequence = identify_sufficiency_risks(
        input_view=input_view,
        consistency_profile=consistency_profile,
        risks=risks,
        sequence=sequence,
        settings=settings,
    )

    risks_by_category: dict[str, int] = {}
    for risk in risks:
        key = risk.risk_category.value
        risks_by_category[key] = risks_by_category.get(key, 0) + 1

    profile = ModelRiskProfile(
        definitive_model_id=evidence_profile.definitive_model_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        group_id=evidence_profile.group_id,
        group_type=evidence_profile.group_type,
        risks=tuple(risks),
        risks_by_category=risks_by_category,
        evidence_records_analyzed=len(evidence_profile.evidence_records),
        inconsistencies_analyzed=len(consistency_profile.inconsistencies),
        source_data_preserved=evidence_profile.source_data_preserved,
    )
    return profile, sequence


def build_risk_catalog(
    *,
    input_view: EvidenceAndConsistencyInputView,
    profiles: tuple[ModelRiskProfile, ...],
    settings: RiskAnalysisEngineSettings,
) -> RiskAnalysisCatalog:
    return RiskAnalysisCatalog(
        catalog_id=f"rae-catalog://{input_view.evidence_catalog.model_id}",
        process_id=input_view.evidence_catalog.process_id,
        model_id=input_view.evidence_catalog.model_id,
        document_id=input_view.evidence_catalog.document_id,
        source_evidence_catalog_id=input_view.evidence_catalog.catalog_id,
        source_consistency_catalog_id=input_view.consistency_catalog.catalog_id,
        profiles=profiles,
        context_evaluation_engine_prepared=settings.context_evaluation_engine_prepared,
        evidence_catalog_preserved=True,
        consistency_catalog_preserved=True,
        source_data_preserved=input_view.evidence_catalog.source_data_preserved,
    )
