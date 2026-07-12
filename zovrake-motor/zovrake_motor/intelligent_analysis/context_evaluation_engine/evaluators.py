"""Utilidades de evaluación contextual de evidencias."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceRecordView,
    ModelEvidenceProfileView,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.enums import (
    ContextAssociationType,
    ContextElementType,
    ContextualGapType,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.gateway import (
    ContextEvaluationInputView,
    RequirementContextView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelView,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextAssociationRecord,
    ContextElementRecord,
    ContextEvaluationCatalog,
    ContextTraceabilityReference,
    ContextualGapRecord,
    ModelContextProfile,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import EvidenceCategory
from zovrake_motor.config.categories.intelligent_analysis import ContextEvaluationEngineSettings

_COMMERCIAL_CATEGORIES = {
    EvidenceCategory.COMMERCIAL_INFORMATION,
    EvidenceCategory.COMMERCIAL_CONDITIONS,
    EvidenceCategory.DELIVERY_TIMES,
}
_TECHNICAL_CATEGORIES = {
    EvidenceCategory.TECHNICAL_INFORMATION,
    EvidenceCategory.CERTIFICATIONS,
    EvidenceCategory.WARRANTIES,
}


def build_public_association_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-A-{sequence:0{padding}d}"


def build_public_gap_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-G-{sequence:0{padding}d}"


def _normalize_key(value: str) -> str:
    return str(value).strip().lower()


def _build_context_traceability(
    *,
    context_key: str,
    context_source: str,
    evidence_profile: ModelEvidenceProfileView,
    document_id: str,
    evidence_id: str | None = None,
    provider_id: str | None = None,
    traceability: dict[str, Any] | None = None,
) -> ContextTraceabilityReference:
    return ContextTraceabilityReference(
        context_key=context_key,
        context_source=context_source,
        evidence_id=evidence_id,
        definitive_model_id=evidence_profile.definitive_model_id,
        group_id=evidence_profile.group_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        provider_id=provider_id,
        document_id=document_id,
        traceability=traceability or {},
    )


def collect_context_elements(
    *,
    requirement_context: RequirementContextView,
    model_view: DefinitiveComparativeModelView,
) -> tuple[ContextElementRecord, ...]:
    elements: list[ContextElementRecord] = []

    if requirement_context.description.strip():
        elements.append(
            ContextElementRecord(
                context_key="description",
                context_value=requirement_context.description,
                element_type=ContextElementType.OBJECTIVE,
                context_source="requirement_context",
            ),
        )

    for key, value in sorted(requirement_context.commercial_requirements.items()):
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        elements.append(
            ContextElementRecord(
                context_key=str(key),
                context_value=value,
                element_type=ContextElementType.COMMERCIAL_REQUIREMENT,
                context_source="requirement_context.commercial_requirements",
            ),
        )

    for key, value in sorted(requirement_context.technical_requirements.items()):
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        elements.append(
            ContextElementRecord(
                context_key=str(key),
                context_value=value,
                element_type=ContextElementType.TECHNICAL_REQUIREMENT,
                context_source="requirement_context.technical_requirements",
            ),
        )

    for key, value in sorted(model_view.inherited_context.items()):
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        element_type = ContextElementType.GENERAL_REQUIREMENT
        normalized = _normalize_key(str(key))
        if "comercial" in normalized or "precio" in normalized or "pago" in normalized:
            element_type = ContextElementType.COMMERCIAL_REQUIREMENT
        elif "tecnico" in normalized or "technical" in normalized or "especific" in normalized:
            element_type = ContextElementType.TECHNICAL_REQUIREMENT
        elif "limit" in normalized or "restric" in normalized:
            element_type = ContextElementType.LIMITATION
        elements.append(
            ContextElementRecord(
                context_key=str(key),
                context_value=value,
                element_type=element_type,
                context_source="definitive_model.inherited_context",
            ),
        )

    return tuple(elements)


def _evidence_matches_context(
    *,
    element: ContextElementRecord,
    record: EvidenceRecordView,
) -> bool:
    context_key = _normalize_key(element.context_key)
    evidence_key = _normalize_key(record.evidence_key)
    if context_key == evidence_key:
        return True
    if context_key in evidence_key or evidence_key in context_key:
        return True
    if str(element.context_value).strip() and str(element.context_value) == str(record.evidence_value):
        return True
    return False


def _relevant_evidence_for_element(
    element: ContextElementRecord,
    evidence_profile: ModelEvidenceProfileView,
) -> list[EvidenceRecordView]:
    if element.element_type in (
        ContextElementType.COMMERCIAL_REQUIREMENT,
        ContextElementType.OBJECTIVE,
    ):
        categories = _COMMERCIAL_CATEGORIES
    elif element.element_type == ContextElementType.TECHNICAL_REQUIREMENT:
        categories = _TECHNICAL_CATEGORIES
    else:
        categories = _COMMERCIAL_CATEGORIES | _TECHNICAL_CATEGORIES | {EvidenceCategory.REQUIREMENT_CONTEXT}

    matches = []
    for record in evidence_profile.evidence_records:
        if record.evidence_category not in categories and element.element_type != ContextElementType.GENERAL_REQUIREMENT:
            continue
        if _evidence_matches_context(element=element, record=record):
            matches.append(record)
    return matches


def evaluate_context_associations(
    *,
    input_view: ContextEvaluationInputView,
    evidence_profile: ModelEvidenceProfileView,
    model_view: DefinitiveComparativeModelView,
    context_elements: tuple[ContextElementRecord, ...],
    associations: list[ContextAssociationRecord],
    sequence: int,
    settings: ContextEvaluationEngineSettings,
) -> int:
    if not (
        settings.detect_commercial_alignment
        or settings.detect_technical_alignment
        or settings.detect_quotation_alignment
    ):
        return sequence

    for element in context_elements:
        matched_records = _relevant_evidence_for_element(element, evidence_profile)
        if matched_records:
            association_type = (
                ContextAssociationType.ALIGNMENT
                if len(matched_records) >= 1
                else ContextAssociationType.PARTIAL_ALIGNMENT
            )
            if element.element_type == ContextElementType.LIMITATION:
                association_type = ContextAssociationType.LIMITATION

            provider_ids = tuple(
                sorted({str(record.provider_id) for record in matched_records if record.provider_id}),
            )
            sequence += 1
            associations.append(
                ContextAssociationRecord(
                    association_id=build_public_association_id(
                        sequence,
                        prefix=settings.association_id_prefix,
                        padding=settings.association_id_padding,
                    ),
                    association_type=association_type,
                    context_key=element.context_key,
                    context_value=element.context_value,
                    element_type=element.element_type,
                    associated_evidence_ids=tuple(record.evidence_id for record in matched_records),
                    provider_ids=provider_ids,
                    traceability_ref=_build_context_traceability(
                        context_key=element.context_key,
                        context_source=element.context_source,
                        evidence_profile=evidence_profile,
                        document_id=input_view.evidence_catalog.document_id,
                        evidence_id=matched_records[0].evidence_id,
                        provider_id=matched_records[0].provider_id,
                        traceability=dict(matched_records[0].traceability_ref.traceability),
                    ),
                    metadata={"element_source": element.context_source},
                ),
            )
    return sequence


def detect_contextual_gaps(
    *,
    input_view: ContextEvaluationInputView,
    evidence_profile: ModelEvidenceProfileView,
    context_elements: tuple[ContextElementRecord, ...],
    associations: list[ContextAssociationRecord],
    gaps: list[ContextualGapRecord],
    sequence: int,
    settings: ContextEvaluationEngineSettings,
) -> int:
    if not settings.detect_context_gaps:
        return sequence

    associated_keys = {_normalize_key(association.context_key) for association in associations}

    for element in context_elements:
        if element.element_type == ContextElementType.LIMITATION:
            continue
        if _normalize_key(element.context_key) in associated_keys:
            continue

        sequence += 1
        gaps.append(
            ContextualGapRecord(
                gap_id=build_public_gap_id(
                    sequence,
                    prefix=settings.gap_id_prefix,
                    padding=settings.gap_id_padding,
                ),
                gap_type=ContextualGapType.REQUIREMENT_WITHOUT_EVIDENCE,
                description=(
                    f"Requisito del contexto '{element.context_key}' sin evidencia suficiente "
                    f"en el Grupo Comparable"
                ),
                context_key=element.context_key,
                related_evidence_ids=(),
                provider_ids=(),
                traceability_ref=_build_context_traceability(
                    context_key=element.context_key,
                    context_source=element.context_source,
                    evidence_profile=evidence_profile,
                    document_id=input_view.evidence_catalog.document_id,
                ),
                metadata={"element_type": element.element_type.value},
            ),
        )

    context_backed_evidence_ids = {
        evidence_id
        for association in associations
        for evidence_id in association.associated_evidence_ids
    }
    for record in evidence_profile.evidence_records:
        if record.evidence_id in context_backed_evidence_ids:
            continue
        if record.evidence_category == EvidenceCategory.METADATA:
            continue
        sequence += 1
        gaps.append(
            ContextualGapRecord(
                gap_id=build_public_gap_id(
                    sequence,
                    prefix=settings.gap_id_prefix,
                    padding=settings.gap_id_padding,
                ),
                gap_type=ContextualGapType.EVIDENCE_WITHOUT_CONTEXT,
                description=(
                    f"Evidencia '{record.evidence_key}' sin respaldo contextual identificado"
                ),
                context_key=record.evidence_key,
                related_evidence_ids=(record.evidence_id,),
                provider_ids=(record.provider_id,) if record.provider_id else (),
                traceability_ref=_build_context_traceability(
                    context_key=record.evidence_key,
                    context_source=record.traceability_ref.source_field,
                    evidence_profile=evidence_profile,
                    document_id=input_view.evidence_catalog.document_id,
                    evidence_id=record.evidence_id,
                    provider_id=record.provider_id,
                    traceability=dict(record.traceability_ref.traceability),
                ),
                metadata={"evidence_category": record.evidence_category.value},
            ),
        )

    if settings.detect_context_limitations and not input_view.requirement_context.description.strip():
        if not context_elements:
            sequence += 1
            gaps.append(
                ContextualGapRecord(
                    gap_id=build_public_gap_id(
                        sequence,
                        prefix=settings.gap_id_prefix,
                        padding=settings.gap_id_padding,
                    ),
                    gap_type=ContextualGapType.INSUFFICIENT_CONTEXT_DATA,
                    description="Contexto del requerimiento insuficiente para evaluación contextual completa",
                    context_key="requirement_context",
                    related_evidence_ids=(),
                    provider_ids=(),
                    traceability_ref=_build_context_traceability(
                        context_key="requirement_context",
                        context_source="requirement_context",
                        evidence_profile=evidence_profile,
                        document_id=input_view.evidence_catalog.document_id,
                    ),
                    metadata={},
                ),
            )

    risk_profile = next(
        (
            profile
            for profile in input_view.risk_catalog.profiles
            if profile.definitive_model_id == evidence_profile.definitive_model_id
        ),
        None,
    )
    if risk_profile and settings.detect_quotation_alignment:
        for risk in risk_profile.risks:
            if "diferencia" in risk.description.lower() or "ausente" in risk.description.lower():
                sequence += 1
                gaps.append(
                    ContextualGapRecord(
                        gap_id=build_public_gap_id(
                            sequence,
                            prefix=settings.gap_id_prefix,
                            padding=settings.gap_id_padding,
                        ),
                        gap_type=ContextualGapType.QUOTATION_REQUIREMENT_DIFFERENCE,
                        description=(
                            f"Diferencia contextual detectada a partir del riesgo: {risk.description}"
                        ),
                        context_key=risk.risk_category.value,
                        related_evidence_ids=risk.associated_evidence_ids,
                        provider_ids=risk.provider_ids,
                        traceability_ref=_build_context_traceability(
                            context_key=risk.risk_category.value,
                            context_source="risk_analysis_engine",
                            evidence_profile=evidence_profile,
                            document_id=input_view.evidence_catalog.document_id,
                            traceability={"risk_id": risk.risk_id},
                        ),
                        metadata={"risk_id": risk.risk_id},
                    ),
                )

    return sequence


def evaluate_profile_context(
    *,
    input_view: ContextEvaluationInputView,
    evidence_profile: ModelEvidenceProfileView,
    model_view: DefinitiveComparativeModelView,
    settings: ContextEvaluationEngineSettings,
    start_sequence: int,
) -> tuple[ModelContextProfile, int]:
    associations: list[ContextAssociationRecord] = []
    gaps: list[ContextualGapRecord] = []
    sequence = start_sequence

    context_elements = collect_context_elements(
        requirement_context=input_view.requirement_context,
        model_view=model_view,
    )

    sequence = evaluate_context_associations(
        input_view=input_view,
        evidence_profile=evidence_profile,
        model_view=model_view,
        context_elements=context_elements,
        associations=associations,
        sequence=sequence,
        settings=settings,
    )
    sequence = detect_contextual_gaps(
        input_view=input_view,
        evidence_profile=evidence_profile,
        context_elements=context_elements,
        associations=associations,
        gaps=gaps,
        sequence=sequence,
        settings=settings,
    )

    profile = ModelContextProfile(
        definitive_model_id=evidence_profile.definitive_model_id,
        comparative_table_id=evidence_profile.comparative_table_id,
        group_id=evidence_profile.group_id,
        group_type=evidence_profile.group_type,
        context_elements=context_elements,
        associations=tuple(associations),
        contextual_gaps=tuple(gaps),
        context_elements_evaluated=len(context_elements),
        evidence_records_evaluated=len(evidence_profile.evidence_records),
        source_data_preserved=evidence_profile.source_data_preserved,
    )
    return profile, sequence


def build_context_catalog(
    *,
    input_view: ContextEvaluationInputView,
    profiles: tuple[ModelContextProfile, ...],
    settings: ContextEvaluationEngineSettings,
) -> ContextEvaluationCatalog:
    return ContextEvaluationCatalog(
        catalog_id=f"cxee-catalog://{input_view.evidence_catalog.model_id}",
        process_id=input_view.evidence_catalog.process_id,
        model_id=input_view.evidence_catalog.model_id,
        document_id=input_view.evidence_catalog.document_id,
        source_evidence_catalog_id=input_view.evidence_catalog.catalog_id,
        source_consistency_catalog_id=input_view.consistency_catalog.catalog_id,
        source_risk_catalog_id=input_view.risk_catalog.catalog_id,
        source_definitive_catalog_id=input_view.definitive_catalog.catalog_id,
        profiles=profiles,
        explanation_generation_engine_prepared=settings.explanation_generation_engine_prepared,
        evidence_catalog_preserved=True,
        consistency_catalog_preserved=True,
        risk_catalog_preserved=True,
        definitive_catalog_preserved=True,
        requirement_context_preserved=True,
        source_data_preserved=input_view.evidence_catalog.source_data_preserved,
    )
