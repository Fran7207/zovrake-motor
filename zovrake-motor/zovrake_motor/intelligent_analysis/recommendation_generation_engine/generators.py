"""Utilidades de generación de recomendaciones basadas en evidencias."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    ModelEvidenceProfileView,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationSectionType,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationSegment,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.enums import (
    ConfidenceLevel,
    RecommendationScenarioType,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.gateway import (
    ModelConsistencyProfileView,
    ModelContextProfileView,
    ModelRiskProfileView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.gateway import (
    ModelExplanationProfileView,
    RecommendationGenerationInputView,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    ModelRecommendationProfile,
    ProviderAlternativeRecord,
    RecommendationGenerationCatalog,
    RecommendationJustificationRecord,
    RecommendationTraceabilityReference,
)
from zovrake_motor.config.categories.intelligent_analysis import RecommendationGenerationEngineSettings


@dataclass(frozen=True)
class ProviderEvidenceSummary:
    """Resumen de evidencias por proveedor — base objetiva de la recomendación."""

    provider_id: str
    evidence_count: int
    strength_count: int
    weakness_count: int
    risk_count: int
    missing_count: int
    supporting_evidence_ids: tuple[str, ...]
    strength_subjects: tuple[str, ...]
    risk_descriptions: tuple[str, ...]
    evidence_score: float


def _collect_provider_summaries(
    *,
    evidence_profile: ModelEvidenceProfileView,
    explanation_profile: ModelExplanationProfileView | None,
    risk_profile: ModelRiskProfileView | None,
) -> dict[str, ProviderEvidenceSummary]:
    providers: dict[str, dict[str, Any]] = {}

    for record in evidence_profile.evidence_records:
        provider_id = record.provider_id or "UNKNOWN"
        entry = providers.setdefault(
            provider_id,
            {
                "evidence_count": 0,
                "strength_count": 0,
                "weakness_count": 0,
                "risk_count": 0,
                "missing_count": 0,
                "supporting_evidence_ids": [],
                "strength_subjects": [],
                "risk_descriptions": [],
            },
        )
        entry["evidence_count"] += 1
        entry["supporting_evidence_ids"].append(record.evidence_id)

    for missing in evidence_profile.missing_evidence_records:
        provider_id = missing.provider_id or "UNKNOWN"
        entry = providers.setdefault(
            provider_id,
            {
                "evidence_count": 0,
                "strength_count": 0,
                "weakness_count": 0,
                "risk_count": 0,
                "missing_count": 0,
                "supporting_evidence_ids": [],
                "strength_subjects": [],
                "risk_descriptions": [],
            },
        )
        entry["missing_count"] += 1

    if explanation_profile is not None:
        for segment in explanation_profile.segments:
            if not isinstance(segment, ExplanationSegment):
                continue
            for provider_id in segment.provider_ids or ("UNKNOWN",):
                entry = providers.setdefault(
                    provider_id,
                    {
                        "evidence_count": 0,
                        "strength_count": 0,
                        "weakness_count": 0,
                        "risk_count": 0,
                        "missing_count": 0,
                        "supporting_evidence_ids": [],
                        "strength_subjects": [],
                        "risk_descriptions": [],
                    },
                )
                if segment.section_type == ExplanationSectionType.STRENGTH:
                    entry["strength_count"] += 1
                    entry["strength_subjects"].append(segment.subject)
                elif segment.section_type == ExplanationSectionType.WEAKNESS:
                    entry["weakness_count"] += 1
                elif segment.section_type == ExplanationSectionType.RISK:
                    entry["risk_count"] += 1
                    facts = segment.structured_content.get("facts", {})
                    if facts.get("description"):
                        entry["risk_descriptions"].append(str(facts["description"]))
                entry["supporting_evidence_ids"].extend(segment.supporting_evidence_ids)

    if risk_profile is not None:
        for risk in risk_profile.risks:
            for provider_id in risk.provider_ids or ("UNKNOWN",):
                entry = providers.setdefault(
                    provider_id,
                    {
                        "evidence_count": 0,
                        "strength_count": 0,
                        "weakness_count": 0,
                        "risk_count": 0,
                        "missing_count": 0,
                        "supporting_evidence_ids": [],
                        "strength_subjects": [],
                        "risk_descriptions": [],
                    },
                )
                entry["risk_count"] += 1
                entry["risk_descriptions"].append(risk.description)
                entry["supporting_evidence_ids"].extend(risk.associated_evidence_ids)

    summaries: dict[str, ProviderEvidenceSummary] = {}
    for provider_id, data in providers.items():
        score = (
            data["evidence_count"]
            + data["strength_count"]
            - data["weakness_count"]
            - data["risk_count"]
            - data["missing_count"]
        )
        summaries[provider_id] = ProviderEvidenceSummary(
            provider_id=provider_id,
            evidence_count=data["evidence_count"],
            strength_count=data["strength_count"],
            weakness_count=data["weakness_count"],
            risk_count=data["risk_count"],
            missing_count=data["missing_count"],
            supporting_evidence_ids=tuple(dict.fromkeys(data["supporting_evidence_ids"])),
            strength_subjects=tuple(dict.fromkeys(data["strength_subjects"])),
            risk_descriptions=tuple(dict.fromkeys(data["risk_descriptions"])),
            evidence_score=float(score),
        )
    return summaries


def _compute_coverage_metrics(
    *,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView | None,
    context_profile: ModelContextProfileView | None,
    risk_profile: ModelRiskProfileView | None,
) -> dict[str, Any]:
    total_evidence = len(evidence_profile.evidence_records)
    total_missing = len(evidence_profile.missing_evidence_records)
    total_items = total_evidence + total_missing
    coverage_ratio = total_evidence / total_items if total_items else 0.0

    return {
        "evidence_coverage_ratio": coverage_ratio,
        "total_evidence": total_evidence,
        "total_missing": total_missing,
        "sufficient_for_reasoning": (
            consistency_profile.sufficient_for_reasoning if consistency_profile else False
        ),
        "blocking_factors": list(consistency_profile.blocking_factors)
        if consistency_profile
        else [],
        "inconsistencies_count": len(consistency_profile.inconsistencies)
        if consistency_profile
        else 0,
        "risks_count": len(risk_profile.risks) if risk_profile else 0,
        "contextual_gaps_count": len(context_profile.contextual_gaps) if context_profile else 0,
    }


def _derive_confidence_level(
    *,
    metrics: dict[str, Any],
    scenario_type: RecommendationScenarioType,
    settings: RecommendationGenerationEngineSettings,
) -> ConfidenceLevel:
    if scenario_type == RecommendationScenarioType.INSUFFICIENT_INFORMATION:
        return ConfidenceLevel.LOW

    coverage = float(metrics["evidence_coverage_ratio"])
    risks = int(metrics["risks_count"])
    gaps = int(metrics["contextual_gaps_count"])
    inconsistencies = int(metrics["inconsistencies_count"])
    sufficient = bool(metrics["sufficient_for_reasoning"])

    if (
        sufficient
        and coverage >= settings.high_confidence_min_coverage
        and risks <= settings.high_confidence_max_risks
        and gaps <= settings.high_confidence_max_context_gaps
        and inconsistencies <= settings.high_confidence_max_inconsistencies
    ):
        return ConfidenceLevel.HIGH

    if coverage >= settings.medium_confidence_min_coverage and sufficient:
        return ConfidenceLevel.MEDIUM

    return ConfidenceLevel.LOW


def _determine_scenario(
    *,
    provider_summaries: dict[str, ProviderEvidenceSummary],
    metrics: dict[str, Any],
    settings: RecommendationGenerationEngineSettings,
) -> RecommendationScenarioType:
    if not metrics["sufficient_for_reasoning"]:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if metrics["blocking_factors"]:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if metrics["total_evidence"] < settings.min_evidence_for_recommendation:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    total_items = metrics["total_evidence"] + metrics["total_missing"]
    if total_items and (metrics["total_missing"] / total_items) > settings.insufficient_missing_ratio:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    ranked = sorted(provider_summaries.values(), key=lambda item: item.evidence_score, reverse=True)
    if not ranked:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if ranked[0].evidence_count < settings.min_evidence_for_recommendation:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if len(ranked) == 1:
        return RecommendationScenarioType.CLEAR_WINNER

    score_gap = ranked[0].evidence_score - ranked[1].evidence_score
    if score_gap >= settings.clear_winner_score_gap:
        return RecommendationScenarioType.CLEAR_WINNER

    within_threshold = [
        provider
        for provider in ranked
        if (ranked[0].evidence_score - provider.evidence_score) <= settings.equivalence_score_threshold
    ]
    if len(within_threshold) >= 2:
        return RecommendationScenarioType.EQUIVALENT_ALTERNATIVES

    return RecommendationScenarioType.CLEAR_WINNER


def _build_traceability(
    *,
    evidence_profile: ModelEvidenceProfileView,
    document_id: str,
    provider_id: str | None,
    evidence_id: str | None = None,
) -> RecommendationTraceabilityReference:
    return RecommendationTraceabilityReference(
        evidence_id=evidence_id,
        risk_id=None,
        inconsistency_id=None,
        missing_evidence_id=None,
        explanation_segment_id=None,
        definitive_model_id=evidence_profile.definitive_model_id,
        group_id=evidence_profile.group_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        provider_id=provider_id,
        document_id=document_id,
        traceability={},
    )


def _collect_limitations_and_missing(
    *,
    explanation_profile: ModelExplanationProfileView | None,
    context_profile: ModelContextProfileView | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    limitations: list[str] = []
    missing_info: list[str] = []
    suggested_actions: list[str] = []

    if explanation_profile is not None:
        for segment in explanation_profile.segments:
            if not isinstance(segment, ExplanationSegment):
                continue
            facts = segment.structured_content.get("facts", {})
            if segment.section_type == ExplanationSectionType.LIMITATION:
                description = facts.get("description") or segment.subject
                limitations.append(str(description))
            elif segment.section_type == ExplanationSectionType.MISSING_INFORMATION:
                key = facts.get("expected_key") or facts.get("context_key") or segment.subject
                missing_info.append(str(key))

    if context_profile is not None:
        for gap in context_profile.contextual_gaps:
            missing_info.append(gap.description)
            if gap.gap_type.value == "insufficient_context_data":
                suggested_actions.append(
                    f"Completar contexto requerido: {gap.context_key}",
                )

    if missing_info:
        suggested_actions.append("Solicitar documentación complementaria para cubrir vacíos detectados")

    return tuple(dict.fromkeys(limitations)), tuple(dict.fromkeys(missing_info)), tuple(dict.fromkeys(suggested_actions))


def generate_model_recommendation_profile(
    *,
    input_view: RecommendationGenerationInputView,
    evidence_profile: ModelEvidenceProfileView,
    consistency_profile: ModelConsistencyProfileView | None,
    risk_profile: ModelRiskProfileView | None,
    context_profile: ModelContextProfileView | None,
    explanation_profile: ModelExplanationProfileView | None,
    settings: RecommendationGenerationEngineSettings,
) -> ModelRecommendationProfile:
    document_id = input_view.evidence_catalog.document_id
    provider_summaries = _collect_provider_summaries(
        evidence_profile=evidence_profile,
        explanation_profile=explanation_profile,
        risk_profile=risk_profile,
    )
    metrics = _compute_coverage_metrics(
        evidence_profile=evidence_profile,
        consistency_profile=consistency_profile,
        context_profile=context_profile,
        risk_profile=risk_profile,
    )
    scenario_type = _determine_scenario(
        provider_summaries=provider_summaries,
        metrics=metrics,
        settings=settings,
    )
    confidence_level = _derive_confidence_level(
        metrics=metrics,
        scenario_type=scenario_type,
        settings=settings,
    )
    limitations, missing_info, suggested_actions = _collect_limitations_and_missing(
        explanation_profile=explanation_profile,
        context_profile=context_profile,
    )

    ranked = sorted(provider_summaries.values(), key=lambda item: item.evidence_score, reverse=True)
    recommended_provider_id: str | None = None
    equivalent_alternatives: list[ProviderAlternativeRecord] = []
    primary_strengths: tuple[str, ...] = ()
    identified_risks: tuple[str, ...] = ()
    supporting_evidence_ids: tuple[str, ...] = ()
    why_issued = ""

    if scenario_type == RecommendationScenarioType.CLEAR_WINNER and ranked:
        best = ranked[0]
        recommended_provider_id = best.provider_id
        primary_strengths = best.strength_subjects
        identified_risks = best.risk_descriptions
        supporting_evidence_ids = best.supporting_evidence_ids
        why_issued = (
            f"Proveedor {best.provider_id} presenta mayor respaldo documental "
            f"(puntuación evidencia: {best.evidence_score})"
        )
    elif scenario_type == RecommendationScenarioType.EQUIVALENT_ALTERNATIVES and ranked:
        top_score = ranked[0].evidence_score
        equivalents = [
            provider
            for provider in ranked
            if (top_score - provider.evidence_score) <= settings.equivalence_score_threshold
        ]
        for provider in equivalents:
            differences = tuple(
                f"Evidencias: {provider.evidence_count}, Riesgos: {provider.risk_count}"
                for _ in [provider]
            )
            equivalent_alternatives.append(
                ProviderAlternativeRecord(
                    provider_id=provider.provider_id,
                    strengths=provider.strength_subjects,
                    relevant_differences=differences,
                    supporting_evidence_ids=provider.supporting_evidence_ids,
                    evidence_score=provider.evidence_score,
                    risk_count=provider.risk_count,
                ),
            )
        supporting_evidence_ids = tuple(
            evidence_id
            for provider in equivalents
            for evidence_id in provider.supporting_evidence_ids
        )
        why_issued = (
            "No existe un proveedor claramente superior; se documentan alternativas equivalentes "
            f"respaldadas por evidencias ({len(equivalents)} proveedores)"
        )
    else:
        why_issued = (
            "La información disponible no permite emitir una recomendación responsable "
            "sin respaldo documental suficiente"
        )
        if not suggested_actions:
            suggested_actions = (
                "Completar documentación de cotizaciones",
                "Verificar consistencia de evidencias",
            )

    remaining_risk_ids = tuple(
        risk.risk_id for risk in (risk_profile.risks if risk_profile else ())
    )

    justification = RecommendationJustificationRecord(
        why_issued=why_issued,
        supporting_evidence_ids=supporting_evidence_ids,
        remaining_risk_ids=remaining_risk_ids,
        limitations=limitations,
        missing_information=missing_info,
        structured_content={
            "template_key": f"recommendation_{scenario_type.value}",
            "facts": {
                "scenario_type": scenario_type.value,
                "confidence_level": confidence_level.value,
                "recommended_provider_id": recommended_provider_id,
                "provider_scores": {
                    provider.provider_id: provider.evidence_score
                    for provider in ranked
                },
                "coverage_metrics": metrics,
            },
        },
    )

    trace_provider = recommended_provider_id or (ranked[0].provider_id if ranked else None)
    first_evidence = supporting_evidence_ids[0] if supporting_evidence_ids else None

    return ModelRecommendationProfile(
        definitive_model_id=evidence_profile.definitive_model_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        group_id=evidence_profile.group_id,
        group_type=evidence_profile.group_type,
        scenario_type=scenario_type,
        confidence_level=confidence_level,
        recommended_provider_id=recommended_provider_id,
        justification=justification,
        primary_strengths=primary_strengths,
        identified_risks=identified_risks,
        limitations=limitations,
        equivalent_alternatives=tuple(equivalent_alternatives),
        suggested_actions=suggested_actions,
        missing_documentation=missing_info,
        supporting_evidence_ids=supporting_evidence_ids,
        traceability_ref=_build_traceability(
            evidence_profile=evidence_profile,
            document_id=document_id,
            provider_id=trace_provider,
            evidence_id=first_evidence,
        ),
        confidence_factors={
            **metrics,
            "scenario_type": scenario_type.value,
            "provider_count": len(provider_summaries),
        },
        source_data_preserved=evidence_profile.source_data_preserved,
    )


def build_recommendation_catalog(
    *,
    input_view: RecommendationGenerationInputView,
    profiles: tuple[ModelRecommendationProfile, ...],
    settings: RecommendationGenerationEngineSettings,
) -> RecommendationGenerationCatalog:
    return RecommendationGenerationCatalog(
        catalog_id=f"rge-catalog://{input_view.evidence_catalog.model_id}",
        process_id=input_view.evidence_catalog.process_id,
        model_id=input_view.evidence_catalog.model_id,
        document_id=input_view.evidence_catalog.document_id,
        source_evidence_catalog_id=input_view.evidence_catalog.catalog_id,
        source_consistency_catalog_id=input_view.consistency_catalog.catalog_id,
        source_risk_catalog_id=input_view.risk_catalog.catalog_id,
        source_context_catalog_id=input_view.context_catalog.catalog_id,
        source_explanation_catalog_id=input_view.explanation_catalog.catalog_id,
        source_definitive_catalog_id=input_view.definitive_catalog.catalog_id,
        profiles=profiles,
        reasoning_result_builder_prepared=settings.reasoning_result_builder_prepared,
        evidence_catalog_preserved=True,
        consistency_catalog_preserved=True,
        risk_catalog_preserved=True,
        context_catalog_preserved=True,
        explanation_catalog_preserved=True,
        definitive_catalog_preserved=True,
        source_data_preserved=input_view.evidence_catalog.source_data_preserved,
    )
