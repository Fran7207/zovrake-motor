"""Utilidades de construcción del Resultado del Análisis Inteligente."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    ModelEvidenceProfileView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationSectionType,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ModelConsistencyProfileView,
    ModelContextProfileView,
    ModelRiskProfileView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    ModelExplanationProfileView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationSegment,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.gateway import (
    ModelRecommendationProfileView,
    ReasoningResultInputView,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    DocumentTraceabilityRecord,
    GroupIntelligentAnalysisResult,
    IntelligentAnalysisResultCatalog,
)
from zovrake_motor.config.categories.intelligent_analysis import ReasoningResultBuilderSettings


def build_public_result_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-R-{sequence:0{padding}d}"


def _extract_executive_summary(
    explanation_profile: ModelExplanationProfileView | None,
) -> dict[str, Any]:
    if explanation_profile is None:
        return {"template_key": "executive_summary_unavailable", "facts": {}}

    for segment in explanation_profile.segments:
        if not isinstance(segment, ExplanationSegment):
            continue
        if segment.section_type == ExplanationSectionType.ANALYSIS_SUMMARY:
            return dict(segment.structured_content)

    return {
        "template_key": "executive_summary_from_explanation_profile",
        "facts": {
            "segments_count": len(explanation_profile.segments),
            "strengths_count": explanation_profile.strengths_count,
            "weaknesses_count": explanation_profile.weaknesses_count,
            "risks_count": explanation_profile.risks_count,
        },
    }


def _extract_structured_explanation(
    explanation_profile: ModelExplanationProfileView | None,
) -> dict[str, Any]:
    if explanation_profile is None:
        return {"segment_ids": [], "sections_summary": {}}

    segment_refs = []
    for segment in explanation_profile.segments:
        if not isinstance(segment, ExplanationSegment):
            continue
        segment_refs.append(
            {
                "segment_id": segment.segment_id,
                "section_type": segment.section_type.value,
                "subject": segment.subject,
                "supporting_evidence_ids": list(segment.supporting_evidence_ids),
            },
        )

    return {
        "segment_ids": [ref["segment_id"] for ref in segment_refs],
        "sections_summary": explanation_profile.raw_profile.sections_summary,
        "segments": segment_refs,
    }


def _extract_recommendation_snapshot(
    recommendation_profile: ModelRecommendationProfileView | None,
) -> dict[str, Any]:
    if recommendation_profile is None:
        return {
            "scenario_type": "unavailable",
            "recommended_provider_id": None,
            "justification": {},
        }

    raw = recommendation_profile.raw_profile
    return {
        "scenario_type": recommendation_profile.scenario_type,
        "confidence_level": recommendation_profile.confidence_level,
        "recommended_provider_id": recommendation_profile.recommended_provider_id,
        "justification": raw.justification.to_dict(),
        "primary_strengths": list(recommendation_profile.primary_strengths),
        "identified_risks": list(recommendation_profile.identified_risks),
        "limitations": list(recommendation_profile.limitations),
        "equivalent_alternatives": [alt.to_dict() for alt in raw.equivalent_alternatives],
        "suggested_actions": list(raw.suggested_actions),
        "missing_documentation": list(raw.missing_documentation),
        "supporting_evidence_ids": list(recommendation_profile.supporting_evidence_ids),
    }


def _extract_strengths_and_weaknesses(
    explanation_profile: ModelExplanationProfileView | None,
    recommendation_profile: ModelRecommendationProfileView | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    strengths: list[str] = []
    weaknesses: list[str] = []

    if recommendation_profile is not None:
        strengths.extend(recommendation_profile.primary_strengths)

    if explanation_profile is not None:
        for segment in explanation_profile.segments:
            if not isinstance(segment, ExplanationSegment):
                continue
            if segment.section_type == ExplanationSectionType.STRENGTH:
                strengths.append(segment.subject)
            elif segment.section_type == ExplanationSectionType.WEAKNESS:
                weaknesses.append(segment.subject)

    return tuple(dict.fromkeys(strengths)), tuple(dict.fromkeys(weaknesses))


def _extract_risks(
    risk_profile: ModelRiskProfileView | None,
    recommendation_profile: ModelRecommendationProfileView | None,
) -> tuple[str, ...]:
    risks: list[str] = []
    if risk_profile is not None:
        risks.extend(risk.description for risk in risk_profile.risks)
    if recommendation_profile is not None:
        risks.extend(recommendation_profile.identified_risks)
    return tuple(dict.fromkeys(risks))


def _extract_limitations(
    explanation_profile: ModelExplanationProfileView | None,
    recommendation_profile: ModelRecommendationProfileView | None,
) -> tuple[str, ...]:
    limitations: list[str] = []
    if recommendation_profile is not None:
        limitations.extend(recommendation_profile.limitations)
    if explanation_profile is not None:
        for segment in explanation_profile.segments:
            if not isinstance(segment, ExplanationSegment):
                continue
            if segment.section_type == ExplanationSectionType.LIMITATION:
                facts = segment.structured_content.get("facts", {})
                limitations.append(str(facts.get("description", segment.subject)))
    return tuple(dict.fromkeys(limitations))


def _extract_context_considered(
    context_profile: ModelContextProfileView | None,
    requirement_context: Any,
) -> dict[str, Any]:
    context_data: dict[str, Any] = {
        "description": getattr(requirement_context, "description", ""),
        "commercial_requirements_count": len(
            getattr(requirement_context, "commercial_requirements", {}),
        ),
        "technical_requirements_count": len(
            getattr(requirement_context, "technical_requirements", {}),
        ),
    }
    if context_profile is not None:
        context_data.update(
            {
                "associations_count": len(context_profile.associations),
                "contextual_gaps_count": len(context_profile.contextual_gaps),
                "context_elements_evaluated": context_profile.context_elements_evaluated,
            },
        )
    return context_data


def _build_document_traceability(
    *,
    evidence_profile: ModelEvidenceProfileView,
    risk_profile: ModelRiskProfileView | None,
    context_profile: ModelContextProfileView | None,
    explanation_profile: ModelExplanationProfileView | None,
    recommendation_profile: ModelRecommendationProfileView | None,
    consistency_profile: ModelConsistencyProfileView | None,
    document_id: str,
) -> DocumentTraceabilityRecord:
    evidence_ids = [record.evidence_id for record in evidence_profile.evidence_records]
    missing_ids = [record.missing_evidence_id for record in evidence_profile.missing_evidence_records]
    risk_ids = [risk.risk_id for risk in risk_profile.risks] if risk_profile else []
    inconsistency_ids = (
        [inc.inconsistency_id for inc in consistency_profile.inconsistencies]
        if consistency_profile
        else []
    )
    segment_ids: list[str] = []
    if explanation_profile is not None:
        for segment in explanation_profile.segments:
            if isinstance(segment, ExplanationSegment):
                segment_ids.append(segment.segment_id)
    association_ids = (
        [assoc.association_id for assoc in context_profile.associations] if context_profile else []
    )
    gap_ids = [gap.gap_id for gap in context_profile.contextual_gaps] if context_profile else []
    provider_ids = list(
        {
            record.provider_id
            for record in evidence_profile.evidence_records
            if record.provider_id
        },
    )
    if recommendation_profile and recommendation_profile.recommended_provider_id:
        provider_ids.append(recommendation_profile.recommended_provider_id)

    return DocumentTraceabilityRecord(
        evidence_ids=tuple(dict.fromkeys(evidence_ids)),
        risk_ids=tuple(dict.fromkeys(risk_ids)),
        inconsistency_ids=tuple(dict.fromkeys(inconsistency_ids)),
        missing_evidence_ids=tuple(dict.fromkeys(missing_ids)),
        explanation_segment_ids=tuple(dict.fromkeys(segment_ids)),
        context_association_ids=tuple(dict.fromkeys(association_ids)),
        contextual_gap_ids=tuple(dict.fromkeys(gap_ids)),
        provider_ids=tuple(dict.fromkeys(provider_ids)),
        definitive_model_id=evidence_profile.definitive_model_id,
        group_id=evidence_profile.group_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        document_id=document_id,
    )


def build_group_intelligent_analysis_result(
    *,
    input_view: ReasoningResultInputView,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView | None,
    risk_profile: ModelRiskProfileView | None,
    context_profile: ModelContextProfileView | None,
    explanation_profile: ModelExplanationProfileView | None,
    recommendation_profile: ModelRecommendationProfileView | None,
    settings: ReasoningResultBuilderSettings,
    sequence: int,
) -> GroupIntelligentAnalysisResult:
    document_id = input_view.evidence_catalog.document_id
    strengths, weaknesses = _extract_strengths_and_weaknesses(
        explanation_profile,
        recommendation_profile,
    )
    recommendation_snapshot = _extract_recommendation_snapshot(recommendation_profile)
    confidence_level = (
        recommendation_profile.confidence_level if recommendation_profile else "low"
    )

    return GroupIntelligentAnalysisResult(
        result_id=build_public_result_id(
            sequence,
            prefix=settings.result_id_prefix,
            padding=settings.result_id_padding,
        ),
        group_id=evidence_profile.group_id,
        definitive_model_id=evidence_profile.definitive_model_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        group_type=evidence_profile.group_type,
        executive_summary=_extract_executive_summary(explanation_profile),
        structured_explanation=_extract_structured_explanation(explanation_profile),
        recommendation=recommendation_snapshot,
        confidence_level=confidence_level,
        strengths=strengths,
        weaknesses=weaknesses,
        risks=_extract_risks(risk_profile, recommendation_profile),
        limitations=_extract_limitations(explanation_profile, recommendation_profile),
        context_considered=_extract_context_considered(
            context_profile,
            input_view.requirement_context,
        ),
        document_traceability=_build_document_traceability(
            evidence_profile=evidence_profile,
            risk_profile=risk_profile,
            context_profile=context_profile,
            explanation_profile=explanation_profile,
            recommendation_profile=recommendation_profile,
            consistency_profile=consistency_profile,
            document_id=document_id,
        ),
        analysis_metadata={
            "process_id": str(input_view.evidence_catalog.process_id),
            "document_id": document_id,
            "model_id": input_view.evidence_catalog.model_id,
            "source_evidence_catalog_id": input_view.evidence_catalog.catalog_id,
            "source_recommendation_catalog_id": input_view.recommendation_catalog.catalog_id,
            "builder": "reasoning_result_builder",
        },
        source_data_preserved=evidence_profile.source_data_preserved,
    )


def build_intelligent_analysis_result_catalog(
    *,
    input_view: ReasoningResultInputView,
    results: tuple[GroupIntelligentAnalysisResult, ...],
    settings: ReasoningResultBuilderSettings,
) -> IntelligentAnalysisResultCatalog:
    return IntelligentAnalysisResultCatalog(
        catalog_id=f"rrb-catalog://{input_view.evidence_catalog.model_id}",
        process_id=input_view.evidence_catalog.process_id,
        model_id=input_view.evidence_catalog.model_id,
        document_id=input_view.evidence_catalog.document_id,
        source_evidence_catalog_id=input_view.evidence_catalog.catalog_id,
        source_consistency_catalog_id=input_view.consistency_catalog.catalog_id,
        source_risk_catalog_id=input_view.risk_catalog.catalog_id,
        source_context_catalog_id=input_view.context_catalog.catalog_id,
        source_explanation_catalog_id=input_view.explanation_catalog.catalog_id,
        source_recommendation_catalog_id=input_view.recommendation_catalog.catalog_id,
        source_definitive_catalog_id=input_view.definitive_catalog.catalog_id,
        results=results,
        integration_certification_framework_prepared=(
            settings.integration_certification_framework_prepared
        ),
        evidence_catalog_preserved=True,
        consistency_catalog_preserved=True,
        risk_catalog_preserved=True,
        context_catalog_preserved=True,
        explanation_catalog_preserved=True,
        recommendation_catalog_preserved=True,
        definitive_catalog_preserved=True,
        source_data_preserved=input_view.evidence_catalog.source_data_preserved,
    )
