"""Utilidades de generación de explicaciones estructuradas basadas en evidencias."""

from __future__ import annotations

from collections import Counter
from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceRecordView,
    MissingEvidenceRecordView,
    ModelEvidenceProfileView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    InconsistencyRecord,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextAssociationRecord,
    ContextualGapRecord,
)

from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationSectionType,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ExplanationGenerationInputView,
    ModelConsistencyProfileView,
    ModelContextProfileView,
    ModelRiskProfileView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationCatalog,
    ExplanationSegment,
    ExplanationTraceabilityReference,
    ModelExplanationProfile,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import RiskRecord
from zovrake_motor.config.categories.intelligent_analysis import ExplanationGenerationEngineSettings


def build_public_segment_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-S-{sequence:0{padding}d}"


def _build_traceability_from_evidence(
    *,
    record: EvidenceRecordView,
    profile_view: ModelEvidenceProfileView,
    document_id: str,
) -> ExplanationTraceabilityReference:
    trace = record.traceability_ref
    return ExplanationTraceabilityReference(
        evidence_id=record.evidence_id,
        risk_id=None,
        inconsistency_id=None,
        missing_evidence_id=None,
        context_association_id=None,
        contextual_gap_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=record.provider_id,
        document_id=document_id,
        traceability=dict(trace.traceability),
    )


def _build_traceability_from_missing(
    *,
    missing: MissingEvidenceRecordView,
    profile_view: ModelEvidenceProfileView,
) -> ExplanationTraceabilityReference:
    return ExplanationTraceabilityReference(
        evidence_id=None,
        risk_id=None,
        inconsistency_id=None,
        missing_evidence_id=missing.missing_evidence_id,
        context_association_id=None,
        contextual_gap_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=missing.provider_id,
        document_id=missing.document_id,
        traceability={},
    )


def _build_traceability_from_inconsistency(
    *,
    inconsistency: InconsistencyRecord,
    profile_view: ModelConsistencyProfileView,
    document_id: str,
) -> ExplanationTraceabilityReference:
    trace = inconsistency.traceability_ref
    return ExplanationTraceabilityReference(
        evidence_id=trace.evidence_id,
        risk_id=None,
        inconsistency_id=inconsistency.inconsistency_id,
        missing_evidence_id=None,
        context_association_id=None,
        contextual_gap_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=trace.provider_id,
        document_id=document_id,
        traceability=dict(trace.traceability),
    )


def _build_traceability_from_risk(
    *,
    risk: RiskRecord,
    profile_view: ModelRiskProfileView,
    document_id: str,
) -> ExplanationTraceabilityReference:
    trace = risk.traceability_ref
    return ExplanationTraceabilityReference(
        evidence_id=trace.evidence_id,
        risk_id=risk.risk_id,
        inconsistency_id=trace.inconsistency_id,
        missing_evidence_id=trace.missing_evidence_id,
        context_association_id=None,
        contextual_gap_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=trace.provider_id,
        document_id=document_id,
        traceability=dict(trace.traceability),
    )


def _build_traceability_from_association(
    *,
    association: ContextAssociationRecord,
    profile_view: ModelContextProfileView,
    document_id: str,
) -> ExplanationTraceabilityReference:
    trace = association.traceability_ref
    return ExplanationTraceabilityReference(
        evidence_id=trace.evidence_id,
        risk_id=None,
        inconsistency_id=None,
        missing_evidence_id=None,
        context_association_id=association.association_id,
        contextual_gap_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=trace.provider_id,
        document_id=document_id,
        traceability=dict(trace.traceability),
    )


def _build_traceability_from_gap(
    *,
    gap: ContextualGapRecord,
    profile_view: ModelContextProfileView,
    document_id: str,
) -> ExplanationTraceabilityReference:
    trace = gap.traceability_ref
    return ExplanationTraceabilityReference(
        evidence_id=trace.evidence_id,
        risk_id=None,
        inconsistency_id=None,
        missing_evidence_id=None,
        context_association_id=None,
        contextual_gap_id=gap.gap_id,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=trace.provider_id,
        document_id=document_id,
        traceability=dict(trace.traceability),
    )


def _append_segment(
    *,
    segments: list[ExplanationSegment],
    sequence: int,
    section_type: ExplanationSectionType,
    subject: str,
    structured_content: dict[str, Any],
    supporting_evidence_ids: tuple[str, ...],
    supporting_risk_ids: tuple[str, ...],
    supporting_inconsistency_ids: tuple[str, ...],
    supporting_context_association_ids: tuple[str, ...],
    supporting_contextual_gap_ids: tuple[str, ...],
    provider_ids: tuple[str, ...],
    traceability_ref: ExplanationTraceabilityReference,
    settings: ExplanationGenerationEngineSettings,
    metadata: dict[str, Any] | None = None,
) -> int:
    sequence += 1
    segments.append(
        ExplanationSegment(
            segment_id=build_public_segment_id(
                sequence,
                prefix=settings.segment_id_prefix,
                padding=settings.segment_id_padding,
            ),
            section_type=section_type,
            subject=subject,
            structured_content=structured_content,
            supporting_evidence_ids=supporting_evidence_ids,
            supporting_risk_ids=supporting_risk_ids,
            supporting_inconsistency_ids=supporting_inconsistency_ids,
            supporting_context_association_ids=supporting_context_association_ids,
            supporting_contextual_gap_ids=supporting_contextual_gap_ids,
            provider_ids=provider_ids,
            traceability_ref=traceability_ref,
            metadata=metadata or {},
        ),
    )
    return sequence


def _generate_evidence_segments(
    *,
    evidence_profile: ModelEvidenceProfileView,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_evidence_sections:
        return sequence

    for record in evidence_profile.evidence_records:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.EVIDENCE_USED,
            subject=record.evidence_key,
            structured_content={
                "template_key": "evidence_used",
                "facts": {
                    "evidence_id": record.evidence_id,
                    "evidence_key": record.evidence_key,
                    "evidence_value": record.evidence_value,
                    "evidence_category": record.evidence_category.value,
                    "provider_id": record.provider_id,
                },
            },
            supporting_evidence_ids=(record.evidence_id,),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=(),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=(record.provider_id,) if record.provider_id else (),
            traceability_ref=_build_traceability_from_evidence(
                record=record,
                profile_view=evidence_profile,
                document_id=document_id,
            ),
            settings=settings,
        )
    return sequence


def _generate_strength_segments(
    *,
    evidence_profile: ModelEvidenceProfileView,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_strength_sections:
        return sequence

    for record in evidence_profile.evidence_records:
        if not record.evidence_value:
            continue
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.STRENGTH,
            subject=record.evidence_key,
            structured_content={
                "template_key": "evidence_present",
                "facts": {
                    "evidence_id": record.evidence_id,
                    "evidence_key": record.evidence_key,
                    "evidence_value": record.evidence_value,
                    "evidence_category": record.evidence_category.value,
                    "provider_id": record.provider_id,
                },
            },
            supporting_evidence_ids=(record.evidence_id,),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=(),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=(record.provider_id,) if record.provider_id else (),
            traceability_ref=_build_traceability_from_evidence(
                record=record,
                profile_view=evidence_profile,
                document_id=document_id,
            ),
            settings=settings,
        )
    return sequence


def _generate_weakness_segments(
    *,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_weakness_sections:
        return sequence

    for missing in evidence_profile.missing_evidence_records:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.WEAKNESS,
            subject=missing.expected_key,
            structured_content={
                "template_key": "missing_evidence",
                "facts": {
                    "missing_evidence_id": missing.missing_evidence_id,
                    "expected_key": missing.expected_key,
                    "reason": missing.reason,
                    "provider_id": missing.provider_id,
                },
            },
            supporting_evidence_ids=(),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=(),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=(missing.provider_id,) if missing.provider_id else (),
            traceability_ref=_build_traceability_from_missing(
                missing=missing,
                profile_view=evidence_profile,
            ),
            settings=settings,
        )

    if consistency_profile is not None:
        for inconsistency in consistency_profile.inconsistencies:
            sequence = _append_segment(
                segments=segments,
                sequence=sequence,
                section_type=ExplanationSectionType.WEAKNESS,
                subject=inconsistency.criterion,
                structured_content={
                    "template_key": "inconsistency_detected",
                    "facts": {
                        "inconsistency_id": inconsistency.inconsistency_id,
                        "inconsistency_type": inconsistency.inconsistency_type.value,
                        "criterion": inconsistency.criterion,
                        "description": inconsistency.description,
                        "related_evidence_ids": list(inconsistency.related_evidence_ids),
                    },
                },
                supporting_evidence_ids=tuple(inconsistency.related_evidence_ids),
                supporting_risk_ids=(),
                supporting_inconsistency_ids=(inconsistency.inconsistency_id,),
                supporting_context_association_ids=(),
                supporting_contextual_gap_ids=(),
                provider_ids=(),
                traceability_ref=_build_traceability_from_inconsistency(
                    inconsistency=inconsistency,
                    profile_view=consistency_profile,
                    document_id=document_id,
                ),
                settings=settings,
            )
    return sequence


def _generate_risk_segments(
    *,
    risk_profile: ModelRiskProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_risk_sections or risk_profile is None:
        return sequence

    for risk in risk_profile.risks:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.RISK,
            subject=risk.risk_category.value,
            structured_content={
                "template_key": "risk_identified",
                "facts": {
                    "risk_id": risk.risk_id,
                    "risk_category": risk.risk_category.value,
                    "description": risk.description,
                    "risk_status": risk.risk_status.value,
                    "associated_evidence_ids": list(risk.associated_evidence_ids),
                    "associated_inconsistency_ids": list(risk.associated_inconsistency_ids),
                },
            },
            supporting_evidence_ids=tuple(risk.associated_evidence_ids),
            supporting_risk_ids=(risk.risk_id,),
            supporting_inconsistency_ids=tuple(risk.associated_inconsistency_ids),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=tuple(risk.provider_ids),
            traceability_ref=_build_traceability_from_risk(
                risk=risk,
                profile_view=risk_profile,
                document_id=document_id,
            ),
            settings=settings,
        )
    return sequence


def _generate_consistency_segments(
    *,
    consistency_profile: ModelConsistencyProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_consistency_sections or consistency_profile is None:
        return sequence

    sequence = _append_segment(
        segments=segments,
        sequence=sequence,
        section_type=ExplanationSectionType.CONSISTENCY,
        subject="sufficiency_assessment",
        structured_content={
            "template_key": "consistency_sufficiency",
            "facts": {
                "sufficiency_level": consistency_profile.sufficiency_level,
                "sufficient_for_reasoning": consistency_profile.sufficient_for_reasoning,
                "blocking_factors": list(consistency_profile.blocking_factors),
                "inconsistencies_count": len(consistency_profile.inconsistencies),
            },
        },
        supporting_evidence_ids=(),
        supporting_risk_ids=(),
        supporting_inconsistency_ids=tuple(
            inc.inconsistency_id for inc in consistency_profile.inconsistencies
        ),
        supporting_context_association_ids=(),
        supporting_contextual_gap_ids=(),
        provider_ids=(),
        traceability_ref=ExplanationTraceabilityReference(
            evidence_id=None,
            risk_id=None,
            inconsistency_id=None,
            missing_evidence_id=None,
            context_association_id=None,
            contextual_gap_id=None,
            definitive_model_id=consistency_profile.definitive_model_id,
            group_id=consistency_profile.group_id,
            comparative_table_id=consistency_profile.comparative_table_id,
            provider_id=None,
            document_id=document_id,
            traceability={},
        ),
        settings=settings,
    )

    for inconsistency in consistency_profile.inconsistencies:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.CONSISTENCY,
            subject=inconsistency.criterion,
            structured_content={
                "template_key": "consistency_inconsistency",
                "facts": {
                    "inconsistency_id": inconsistency.inconsistency_id,
                    "inconsistency_type": inconsistency.inconsistency_type.value,
                    "criterion": inconsistency.criterion,
                    "description": inconsistency.description,
                },
            },
            supporting_evidence_ids=tuple(inconsistency.related_evidence_ids),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=(inconsistency.inconsistency_id,),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=(),
            traceability_ref=_build_traceability_from_inconsistency(
                inconsistency=inconsistency,
                profile_view=consistency_profile,
                document_id=document_id,
            ),
            settings=settings,
        )
    return sequence


def _generate_context_segments(
    *,
    context_profile: ModelContextProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_context_sections or context_profile is None:
        return sequence

    for association in context_profile.associations:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.CONTEXT_INFLUENCE,
            subject=association.context_key,
            structured_content={
                "template_key": "context_association",
                "facts": {
                    "association_id": association.association_id,
                    "association_type": association.association_type.value,
                    "context_key": association.context_key,
                    "context_value": association.context_value,
                    "element_type": association.element_type.value,
                    "associated_evidence_ids": list(association.associated_evidence_ids),
                },
            },
            supporting_evidence_ids=tuple(association.associated_evidence_ids),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=(),
            supporting_context_association_ids=(association.association_id,),
            supporting_contextual_gap_ids=(),
            provider_ids=tuple(association.provider_ids),
            traceability_ref=_build_traceability_from_association(
                association=association,
                profile_view=context_profile,
                document_id=document_id,
            ),
            settings=settings,
        )
    return sequence


def _generate_missing_info_segments(
    *,
    evidence_profile: ModelEvidenceProfileView,
    context_profile: ModelContextProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_missing_information_sections:
        return sequence

    for missing in evidence_profile.missing_evidence_records:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.MISSING_INFORMATION,
            subject=missing.expected_key,
            structured_content={
                "template_key": "missing_evidence_information",
                "facts": {
                    "missing_evidence_id": missing.missing_evidence_id,
                    "expected_key": missing.expected_key,
                    "reason": missing.reason,
                },
            },
            supporting_evidence_ids=(),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=(),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=(missing.provider_id,) if missing.provider_id else (),
            traceability_ref=_build_traceability_from_missing(
                missing=missing,
                profile_view=evidence_profile,
            ),
            settings=settings,
        )

    if context_profile is not None:
        for gap in context_profile.contextual_gaps:
            sequence = _append_segment(
                segments=segments,
                sequence=sequence,
                section_type=ExplanationSectionType.MISSING_INFORMATION,
                subject=gap.context_key,
                structured_content={
                    "template_key": "contextual_gap",
                    "facts": {
                        "gap_id": gap.gap_id,
                        "gap_type": gap.gap_type.value,
                        "description": gap.description,
                        "context_key": gap.context_key,
                    },
                },
                supporting_evidence_ids=tuple(gap.related_evidence_ids),
                supporting_risk_ids=(),
                supporting_inconsistency_ids=(),
                supporting_context_association_ids=(),
                supporting_contextual_gap_ids=(gap.gap_id,),
                provider_ids=tuple(gap.provider_ids),
                traceability_ref=_build_traceability_from_gap(
                    gap=gap,
                    profile_view=context_profile,
                    document_id=document_id,
                ),
                settings=settings,
            )
    return sequence


def _generate_limitation_segments(
    *,
    consistency_profile: ModelConsistencyProfileView | None,
    context_profile: ModelContextProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_limitation_sections:
        return sequence

    if consistency_profile is not None and not consistency_profile.sufficient_for_reasoning:
        sequence = _append_segment(
            segments=segments,
            sequence=sequence,
            section_type=ExplanationSectionType.LIMITATION,
            subject="consistency_sufficiency",
            structured_content={
                "template_key": "insufficient_consistency",
                "facts": {
                    "sufficiency_level": consistency_profile.sufficiency_level,
                    "blocking_factors": list(consistency_profile.blocking_factors),
                },
            },
            supporting_evidence_ids=(),
            supporting_risk_ids=(),
            supporting_inconsistency_ids=tuple(
                inc.inconsistency_id for inc in consistency_profile.inconsistencies
            ),
            supporting_context_association_ids=(),
            supporting_contextual_gap_ids=(),
            provider_ids=(),
            traceability_ref=ExplanationTraceabilityReference(
                evidence_id=None,
                risk_id=None,
                inconsistency_id=None,
                missing_evidence_id=None,
                context_association_id=None,
                contextual_gap_id=None,
                definitive_model_id=consistency_profile.definitive_model_id,
                group_id=consistency_profile.group_id,
                comparative_table_id=consistency_profile.comparative_table_id,
                provider_id=None,
                document_id=document_id,
                traceability={},
            ),
            settings=settings,
        )

    if context_profile is not None:
        for gap in context_profile.contextual_gaps:
            if gap.gap_type.value in (
                "insufficient_context_data",
                "quotation_requirement_difference",
            ):
                sequence = _append_segment(
                    segments=segments,
                    sequence=sequence,
                    section_type=ExplanationSectionType.LIMITATION,
                    subject=gap.context_key,
                    structured_content={
                        "template_key": "context_limitation",
                        "facts": {
                            "gap_id": gap.gap_id,
                            "gap_type": gap.gap_type.value,
                            "description": gap.description,
                        },
                    },
                    supporting_evidence_ids=tuple(gap.related_evidence_ids),
                    supporting_risk_ids=(),
                    supporting_inconsistency_ids=(),
                    supporting_context_association_ids=(),
                    supporting_contextual_gap_ids=(gap.gap_id,),
                    provider_ids=tuple(gap.provider_ids),
                    traceability_ref=_build_traceability_from_gap(
                        gap=gap,
                        profile_view=context_profile,
                        document_id=document_id,
                    ),
                    settings=settings,
                )
    return sequence


def _generate_summary_segment(
    *,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView | None,
    risk_profile: ModelRiskProfileView | None,
    context_profile: ModelContextProfileView | None,
    segments: list[ExplanationSegment],
    sequence: int,
    document_id: str,
    settings: ExplanationGenerationEngineSettings,
) -> int:
    if not settings.generate_summary_sections:
        return sequence

    return _append_segment(
        segments=segments,
        sequence=sequence,
        section_type=ExplanationSectionType.ANALYSIS_SUMMARY,
        subject="model_analysis_summary",
        structured_content={
            "template_key": "analysis_summary",
            "facts": {
                "definitive_model_id": evidence_profile.definitive_model_id,
                "group_id": evidence_profile.group_id,
                "evidence_records_count": len(evidence_profile.evidence_records),
                "missing_evidence_count": len(evidence_profile.missing_evidence_records),
                "inconsistencies_count": (
                    len(consistency_profile.inconsistencies) if consistency_profile else 0
                ),
                "risks_count": len(risk_profile.risks) if risk_profile else 0,
                "context_associations_count": (
                    len(context_profile.associations) if context_profile else 0
                ),
                "contextual_gaps_count": (
                    len(context_profile.contextual_gaps) if context_profile else 0
                ),
            },
        },
        supporting_evidence_ids=tuple(
            record.evidence_id for record in evidence_profile.evidence_records
        ),
        supporting_risk_ids=tuple(risk.risk_id for risk in risk_profile.risks)
        if risk_profile
        else (),
        supporting_inconsistency_ids=tuple(
            inc.inconsistency_id for inc in consistency_profile.inconsistencies
        )
        if consistency_profile
        else (),
        supporting_context_association_ids=tuple(
            assoc.association_id for assoc in context_profile.associations
        )
        if context_profile
        else (),
        supporting_contextual_gap_ids=tuple(gap.gap_id for gap in context_profile.contextual_gaps)
        if context_profile
        else (),
        provider_ids=(),
        traceability_ref=ExplanationTraceabilityReference(
            evidence_id=None,
            risk_id=None,
            inconsistency_id=None,
            missing_evidence_id=None,
            context_association_id=None,
            contextual_gap_id=None,
            definitive_model_id=evidence_profile.definitive_model_id,
            group_id=evidence_profile.group_id,
            comparative_table_id=evidence_profile.comparative_table_id,
            provider_id=None,
            document_id=document_id,
            traceability={},
        ),
        settings=settings,
    )


def generate_model_explanation_profile(
    *,
    input_view: ExplanationGenerationInputView,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView | None,
    risk_profile: ModelRiskProfileView | None,
    context_profile: ModelContextProfileView | None,
    settings: ExplanationGenerationEngineSettings,
    start_sequence: int,
) -> tuple[ModelExplanationProfile, int]:
    segments: list[ExplanationSegment] = []
    sequence = start_sequence
    document_id = input_view.evidence_catalog.document_id

    sequence = _generate_summary_segment(
        evidence_profile=evidence_profile,
        consistency_profile=consistency_profile,
        risk_profile=risk_profile,
        context_profile=context_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_evidence_segments(
        evidence_profile=evidence_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_strength_segments(
        evidence_profile=evidence_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_weakness_segments(
        evidence_profile=evidence_profile,
        consistency_profile=consistency_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_risk_segments(
        risk_profile=risk_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_consistency_segments(
        consistency_profile=consistency_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_context_segments(
        context_profile=context_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_missing_info_segments(
        evidence_profile=evidence_profile,
        context_profile=context_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )
    sequence = _generate_limitation_segments(
        consistency_profile=consistency_profile,
        context_profile=context_profile,
        segments=segments,
        sequence=sequence,
        document_id=document_id,
        settings=settings,
    )

    section_counts = Counter(segment.section_type.value for segment in segments)
    profile = ModelExplanationProfile(
        definitive_model_id=evidence_profile.definitive_model_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        group_id=evidence_profile.group_id,
        group_type=evidence_profile.group_type,
        segments=tuple(segments),
        sections_summary=dict(section_counts),
        evidence_segments_count=section_counts.get(ExplanationSectionType.EVIDENCE_USED.value, 0),
        strengths_count=section_counts.get(ExplanationSectionType.STRENGTH.value, 0),
        weaknesses_count=section_counts.get(ExplanationSectionType.WEAKNESS.value, 0),
        risks_count=section_counts.get(ExplanationSectionType.RISK.value, 0),
        source_data_preserved=evidence_profile.source_data_preserved,
    )
    return profile, sequence


def build_explanation_catalog(
    *,
    input_view: ExplanationGenerationInputView,
    profiles: tuple[ModelExplanationProfile, ...],
    settings: ExplanationGenerationEngineSettings,
) -> ExplanationGenerationCatalog:
    return ExplanationGenerationCatalog(
        catalog_id=f"ege-catalog://{input_view.evidence_catalog.model_id}",
        process_id=input_view.evidence_catalog.process_id,
        model_id=input_view.evidence_catalog.model_id,
        document_id=input_view.evidence_catalog.document_id,
        source_evidence_catalog_id=input_view.evidence_catalog.catalog_id,
        source_consistency_catalog_id=input_view.consistency_catalog.catalog_id,
        source_risk_catalog_id=input_view.risk_catalog.catalog_id,
        source_context_catalog_id=input_view.context_catalog.catalog_id,
        source_definitive_catalog_id=input_view.definitive_catalog.catalog_id,
        profiles=profiles,
        recommendation_generation_engine_prepared=settings.recommendation_generation_engine_prepared,
        conclusion_generation_engine_prepared=settings.conclusion_generation_engine_prepared,
        evidence_catalog_preserved=True,
        consistency_catalog_preserved=True,
        risk_catalog_preserved=True,
        context_catalog_preserved=True,
        definitive_catalog_preserved=True,
        source_data_preserved=input_view.evidence_catalog.source_data_preserved,
    )
