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


def _definitive_catalog_dict(
    definitive_catalog: Any,
) -> dict[str, Any]:
    """Obtiene una representación dict del catálogo definitivo sin acoplar PM7."""
    if isinstance(
        definitive_catalog,
        dict,
    ):
        return definitive_catalog

    to_dict = getattr(
        definitive_catalog,
        "to_dict",
        None,
    )

    if callable(to_dict):
        result = to_dict()
        if isinstance(
            result,
            dict,
        ):
            return result

    return {}


def _models_from_definitive_catalog(
    definitive_catalog: Any,
) -> tuple[dict[str, Any], ...]:
    raw = _definitive_catalog_dict(
        definitive_catalog
    ).get(
        "models",
        (),
    )

    if not isinstance(
        raw,
        (list, tuple),
    ):
        return ()

    return tuple(
        model
        for model in raw
        if isinstance(
            model,
            dict,
        )
    )


def _normal_text(
    value: Any,
) -> str:
    return " ".join(
        str(value)
        .casefold()
        .replace(
            "_",
            " ",
        )
        .split()
    )


def _provider_rows_for_model(
    model: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = model.get(
        "dynamic_rows",
        (),
    )

    if not isinstance(
        rows,
        (list, tuple),
    ):
        return {}

    result: dict[str, dict[str, Any]] = {}

    for row in rows:
        if not isinstance(
            row,
            dict,
        ):
            continue

        provider_id = str(
            row.get(
                "provider_id",
                "",
            )
        ).strip()

        if not provider_id:
            continue

        result[provider_id] = row

    return result


def _row_values(
    row: dict[str, Any],
) -> dict[str, Any]:
    values = row.get(
        "values",
        {},
    )

    if isinstance(
        values,
        dict,
    ):
        return values

    result: dict[str, Any] = {}

    cells = row.get(
        "cells",
        (),
    )

    if isinstance(
        cells,
        (list, tuple),
    ):
        for cell in cells:
            if not isinstance(
                cell,
                dict,
            ):
                continue

            key = str(
                cell.get(
                    "attribute_name",
                    cell.get(
                        "column_id",
                        "",
                    ),
                )
            ).strip()

            if key:
                result[key] = cell.get(
                    "value",
                )

    return result


def _numeric(
    value: Any,
) -> float | None:
    if value is None:
        return None

    text = str(
        value
    ).strip()

    if not text:
        return None

    cleaned = re.sub(
        r"[^0-9,.\-+]",
        "",
        text,
    )

    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(
                ".",
                "",
            ).replace(
                ",",
                ".",
            )
        else:
            cleaned = cleaned.replace(
                ",",
                "",
            )
    elif "," in cleaned:
        parts = cleaned.split(",")
        if (
            len(parts) == 2
            and len(parts[1]) <= 2
        ):
            cleaned = cleaned.replace(
                ",",
                ".",
            )
        else:
            cleaned = cleaned.replace(
                ",",
                "",
            )

    try:
        return float(cleaned)
    except ValueError:
        return None


def _first_numeric_field(
    values: dict[str, Any],
    *,
    keywords: tuple[str, ...],
) -> tuple[str, float] | None:
    for name, value in values.items():
        normalized_name = _normal_text(
            name
        )

        if not any(
            keyword in normalized_name
            for keyword in keywords
        ):
            continue

        parsed = _numeric(
            value
        )

        if parsed is not None:
            return (
                str(name),
                parsed,
            )

    return None


def _provider_matrix_metrics(
    *,
    definitive_catalog: Any,
    definitive_model_id: str,
) -> dict[str, dict[str, Any]]:
    models = _models_from_definitive_catalog(
        definitive_catalog
    )

    target_model = next(
        (
            model
            for model in models
            if str(
                model.get(
                    "definitive_model_id",
                    "",
                )
            )
            == definitive_model_id
        ),
        None,
    )

    if target_model is None:
        return {}

    rows = _provider_rows_for_model(
        target_model
    )

    metrics: dict[str, dict[str, Any]] = {}

    for provider_id, row in rows.items():
        values = _row_values(
            row
        )

        price = _first_numeric_field(
            values,
            keywords=(
                "precio unitario",
                "unit price",
                "p unit",
                "precio",
                "price",
                "precio neto",
                "net price",
                "subtotal",
                "total",
            ),
        )

        delivery = _first_numeric_field(
            values,
            keywords=(
                "entrega",
                "delivery",
                "dias",
                "days",
                "plazo",
            ),
        )

        discount = _first_numeric_field(
            values,
            keywords=(
                "descuento",
                "discount",
            ),
        )

        present_values = sum(
            1
            for value in values.values()
            if str(
                value
            ).strip()
        )

        metrics[provider_id] = {
            "provider_name": str(
                row.get(
                    "provider_name",
                    provider_id,
                )
            ).strip()
            or provider_id,
            "price_field": (
                price[0]
                if price
                else None
            ),
            "price": (
                price[1]
                if price
                else None
            ),
            "delivery_field": (
                delivery[0]
                if delivery
                else None
            ),
            "delivery_days": (
                delivery[1]
                if delivery
                else None
            ),
            "discount_field": (
                discount[0]
                if discount
                else None
            ),
            "discount": (
                discount[1]
                if discount
                else None
            ),
            "values_present": present_values,
            "values_total": len(
                values
            ),
            "source_item_id": str(
                row.get(
                    "source_item_id",
                    "",
                )
            ),
            "source_document_id": str(
                row.get(
                    "document_id",
                    "",
                )
            ),
        }

    return metrics


def _matrix_provider_score(
    *,
    metrics: dict[str, Any],
    all_metrics: tuple[dict[str, Any], ...],
    evidence_summary: ProviderEvidenceSummary | None,
) -> tuple[float, tuple[str, ...]]:
    """
    Calcula una puntuación de decisión explicable.

    Las señales monetarias se comparan únicamente cuando existen para varios
    proveedores. La cobertura y los riesgos actúan como moderadores; no se
    permite que el conteo bruto de evidencias sea el ganador por sí mismo.
    """
    score = 0.0
    reasons: list[str] = []

    prices = [
        item["price"]
        for item in all_metrics
        if item["price"] is not None
    ]

    if metrics["price"] is not None and len(prices) >= 2:
        minimum = min(prices)
        maximum = max(prices)

        if maximum > minimum:
            price_score = (
                (maximum - metrics["price"])
                / (maximum - minimum)
            )
        else:
            price_score = 1.0

        score += 0.55 * price_score

        if metrics["price"] == minimum:
            reasons.append(
                "lowest_comparable_price"
            )

    delivery_values = [
        item["delivery_days"]
        for item in all_metrics
        if item["delivery_days"] is not None
    ]

    if (
        metrics["delivery_days"] is not None
        and len(delivery_values) >= 2
    ):
        minimum = min(
            delivery_values
        )
        maximum = max(
            delivery_values
        )

        if maximum > minimum:
            delivery_score = (
                (maximum - metrics["delivery_days"])
                / (maximum - minimum)
            )
        else:
            delivery_score = 1.0

        score += 0.10 * delivery_score

        if metrics["delivery_days"] == minimum:
            reasons.append(
                "shortest_documented_delivery"
            )

    discount_values = [
        item["discount"]
        for item in all_metrics
        if item["discount"] is not None
    ]

    if (
        metrics["discount"] is not None
        and len(discount_values) >= 2
    ):
        minimum = min(
            discount_values
        )
        maximum = max(
            discount_values
        )

        if maximum > minimum:
            discount_score = (
                (metrics["discount"] - minimum)
                / (maximum - minimum)
            )
        else:
            discount_score = 1.0

        score += 0.05 * discount_score

    coverage = (
        metrics["values_present"]
        / metrics["values_total"]
        if metrics["values_total"]
        else 0.0
    )

    score += 0.15 * coverage

    if coverage >= 0.80:
        reasons.append(
            "high_comparison_field_coverage"
        )
    elif coverage >= 0.50:
        reasons.append(
            "moderate_comparison_field_coverage"
        )

    risk_count = (
        evidence_summary.risk_count
        if evidence_summary is not None
        else 0
    )

    risk_penalty = min(
        0.15,
        risk_count * 0.05,
    )

    score += 0.15 - risk_penalty

    if risk_count == 0:
        reasons.append(
            "no_registered_provider_risks"
        )
    else:
        reasons.append(
            f"risk_penalty={risk_penalty:.2f}"
        )

    if (
        evidence_summary is not None
        and evidence_summary.missing_count == 0
    ):
        reasons.append(
            "no_missing_provider_evidence"
        )

    return (
        max(
            0.0,
            min(
                1.0,
                score,
            ),
        ),
        tuple(
            dict.fromkeys(
                reasons
            )
        ),
    )


def _matrix_aware_provider_ranking(
    *,
    input_view: RecommendationGenerationInputView,
    evidence_profile: ModelEvidenceProfileView,
    provider_summaries: dict[str, ProviderEvidenceSummary],
) -> tuple[
    tuple[ProviderEvidenceSummary, ...],
    dict[str, dict[str, Any]],
]:
    metrics_by_provider = _provider_matrix_metrics(
        definitive_catalog=input_view.definitive_catalog,
        definitive_model_id=evidence_profile.definitive_model_id,
    )

    if len(
        metrics_by_provider
    ) < 2:
        return (
            tuple(
                sorted(
                    provider_summaries.values(),
                    key=lambda item: item.evidence_score,
                    reverse=True,
                )
            ),
            {},
        )

    matrix_metrics = tuple(
        metrics_by_provider.values()
    )

    ranked_raw: list[
        tuple[
            ProviderEvidenceSummary,
            float,
        ]
    ] = []

    decision_metadata: dict[str, dict[str, Any]] = {}

    for provider_id, metrics in metrics_by_provider.items():
        evidence_summary = provider_summaries.get(
            provider_id
        )

        score, reasons = _matrix_provider_score(
            metrics=metrics,
            all_metrics=matrix_metrics,
            evidence_summary=evidence_summary,
        )

        if evidence_summary is None:
            evidence_summary = ProviderEvidenceSummary(
                provider_id=provider_id,
                evidence_count=0,
                strength_count=0,
                weakness_count=0,
                risk_count=0,
                missing_count=0,
                supporting_evidence_ids=(),
                strength_subjects=(),
                risk_descriptions=(),
                evidence_score=0.0,
            )

        ranked_raw.append(
            (
                evidence_summary,
                score,
            )
        )

        decision_metadata[
            provider_id
        ] = {
            "decision_score": round(
                score,
                4,
            ),
            "decision_reasons": list(
                reasons
            ),
            "matrix_metrics": metrics,
        }

    ranked_raw.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return (
        tuple(
            item[0]
            for item in ranked_raw
        ),
        decision_metadata,
    )


def _determine_scenario(
    *,
    provider_summaries: dict[str, ProviderEvidenceSummary],
    metrics: dict[str, Any],
    settings: RecommendationGenerationEngineSettings,
    definitive_catalog: Any | None = None,
    definitive_model_id: str = "",
) -> RecommendationScenarioType:
    """
    Determina el escenario teniendo en cuenta la existencia real de
    proveedores comparables.

    Una sola oferta nunca es un ganador competitivo.
    """
    if not metrics["sufficient_for_reasoning"]:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if metrics["blocking_factors"]:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    provider_count = len(
        provider_summaries
    )

    if provider_count < 2:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if (
        metrics["total_evidence"]
        < settings.min_evidence_for_recommendation
    ):
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    total_items = (
        metrics["total_evidence"]
        + metrics["total_missing"]
    )

    if (
        total_items
        and (
            metrics["total_missing"]
            / total_items
        )
        > settings.insufficient_missing_ratio
    ):
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if definitive_catalog is not None:
        matrix_metrics = _provider_matrix_metrics(
            definitive_catalog=definitive_catalog,
            definitive_model_id=definitive_model_id,
        )

        if len(
            matrix_metrics
        ) >= 2:
            scores = []
            for provider_id, provider_metrics in matrix_metrics.items():
                summary = provider_summaries.get(
                    provider_id
                )

                score, _ = _matrix_provider_score(
                    metrics=provider_metrics,
                    all_metrics=tuple(
                        matrix_metrics.values()
                    ),
                    evidence_summary=summary,
                )

                scores.append(
                    (
                        provider_id,
                        score,
                    )
                )

            scores.sort(
                key=lambda item: item[1],
                reverse=True,
            )

            if not scores:
                return RecommendationScenarioType.INSUFFICIENT_INFORMATION

            if len(scores) >= 2:
                gap = (
                    scores[0][1]
                    - scores[1][1]
                )

                if (
                    gap
                    >= settings.clear_winner_score_gap
                    / 10
                ):
                    return RecommendationScenarioType.CLEAR_WINNER

                if (
                    gap
                    <= (
                        settings.equivalence_score_threshold
                        / 10
                    )
                ):
                    return RecommendationScenarioType.EQUIVALENT_ALTERNATIVES

    ranked = sorted(
        provider_summaries.values(),
        key=lambda item: item.evidence_score,
        reverse=True,
    )

    if not ranked:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    if len(ranked) == 1:
        return RecommendationScenarioType.INSUFFICIENT_INFORMATION

    score_gap = (
        ranked[0].evidence_score
        - ranked[1].evidence_score
    )

    if score_gap >= settings.clear_winner_score_gap:
        return RecommendationScenarioType.CLEAR_WINNER

    within_threshold = [
        provider
        for provider in ranked
        if (
            ranked[0].evidence_score
            - provider.evidence_score
        )
        <= settings.equivalence_score_threshold
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
    ranked_summaries, decision_metadata = (
        _matrix_aware_provider_ranking(
            input_view=input_view,
            evidence_profile=evidence_profile,
            provider_summaries=provider_summaries,
        )
    )

    if ranked_summaries:
        provider_summaries_for_decision = {
            item.provider_id: item
            for item in ranked_summaries
        }
    else:
        provider_summaries_for_decision = provider_summaries

    scenario_type = _determine_scenario(
        provider_summaries=provider_summaries_for_decision,
        metrics=metrics,
        settings=settings,
        definitive_catalog=input_view.definitive_catalog,
        definitive_model_id=evidence_profile.definitive_model_id,
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

    ranked = list(
        ranked_summaries
        or tuple(
            sorted(
                provider_summaries.values(),
                key=lambda item: item.evidence_score,
                reverse=True,
            )
        )
    )
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
                "matrix_decision_scores": {
                    provider_id: details["decision_score"]
                    for provider_id, details in decision_metadata.items()
                },
                "matrix_decision_reasons": {
                    provider_id: details["decision_reasons"]
                    for provider_id, details in decision_metadata.items()
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
            "provider_count": len(provider_summaries_for_decision),
            "matrix_aware": bool(
                decision_metadata
            ),
            "matrix_provider_count": len(
                decision_metadata
            ),
            "matrix_decision_scores": {
                provider_id: details["decision_score"]
                for provider_id, details in decision_metadata.items()
            },
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
