"""Utilidades de evaluación de consistencia de evidencias."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyCriterionType,
    InconsistencyType,
    SufficiencyLevel,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.gateway import (
    EvidenceAnalysisCatalogView,
    EvidenceRecordView,
    ModelEvidenceProfileView,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationCatalog,
    InconsistencyRecord,
    InconsistencyTraceabilityReference,
    ModelConsistencyProfile,
    SufficiencyAssessment,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import EvidenceCategory
from zovrake_motor.config.categories.intelligent_analysis import ConsistencyEvaluationEngineSettings

_COMMERCIAL_CATEGORIES = {
    EvidenceCategory.COMMERCIAL_INFORMATION,
    EvidenceCategory.COMMERCIAL_CONDITIONS,
}
_TECHNICAL_CATEGORIES = {
    EvidenceCategory.TECHNICAL_INFORMATION,
}


def build_public_inconsistency_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def _normalize_key(value: str) -> str:
    return str(value).strip().lower()


def _build_inconsistency_traceability(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    record: EvidenceRecordView | None = None,
    provider_id: str | None = None,
) -> InconsistencyTraceabilityReference:
    if record is not None:
        trace = record.traceability_ref
        return InconsistencyTraceabilityReference(
            evidence_id=record.evidence_id,
            definitive_model_id=trace.definitive_model_id,
            group_id=trace.group_id,
            comparative_table_id=trace.comparative_table_id,
            provider_id=trace.provider_id,
            document_id=trace.document_id,
            source_field=trace.source_field,
            traceability=dict(trace.traceability),
        )
    return InconsistencyTraceabilityReference(
        evidence_id=None,
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        comparative_table_id=profile_view.comparative_table_id,
        provider_id=provider_id,
        document_id=catalog_view.document_id,
        source_field=None,
        traceability={},
    )


def _append_inconsistency(
    *,
    inconsistencies: list[InconsistencyRecord],
    sequence: int,
    inconsistency_type: InconsistencyType,
    criterion: ConsistencyCriterionType,
    description: str,
    related_evidence_ids: tuple[str, ...],
    provider_ids: tuple[str, ...],
    traceability_ref: InconsistencyTraceabilityReference,
    settings: ConsistencyEvaluationEngineSettings,
    metadata: dict[str, Any] | None = None,
) -> int:
    sequence += 1
    inconsistencies.append(
        InconsistencyRecord(
            inconsistency_id=build_public_inconsistency_id(
                sequence,
                prefix=settings.inconsistency_id_prefix,
                padding=settings.inconsistency_id_padding,
            ),
            inconsistency_type=inconsistency_type,
            criterion=criterion,
            description=description,
            related_evidence_ids=related_evidence_ids,
            provider_ids=provider_ids,
            traceability_ref=traceability_ref,
            metadata=metadata or {},
        ),
    )
    return sequence


def _records_by_provider_and_key(
    records: tuple[EvidenceRecordView, ...],
) -> dict[str | None, dict[str, list[EvidenceRecordView]]]:
    grouped: dict[str | None, dict[str, list[EvidenceRecordView]]] = {}
    for record in records:
        provider_bucket = grouped.setdefault(record.provider_id, {})
        key = _normalize_key(record.evidence_key)
        provider_bucket.setdefault(key, []).append(record)
    return grouped


def evaluate_information_integrity(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    inconsistencies: list[InconsistencyRecord],
    sequence: int,
    settings: ConsistencyEvaluationEngineSettings,
) -> int:
    if not settings.detect_integrity_violations:
        return sequence

    for record in profile_view.evidence_records:
        trace = record.traceability_ref
        if trace.definitive_model_id != profile_view.definitive_model_id:
            sequence = _append_inconsistency(
                inconsistencies=inconsistencies,
                sequence=sequence,
                inconsistency_type=InconsistencyType.INCOMPLETE_REFERENCE,
                criterion=ConsistencyCriterionType.INFORMATION_INTEGRITY,
                description=(
                    "Referencia de trazabilidad con definitive_model_id distinto al perfil evaluado"
                ),
                related_evidence_ids=(record.evidence_id,),
                provider_ids=(record.provider_id,) if record.provider_id else (),
                traceability_ref=_build_inconsistency_traceability(
                    catalog_view=catalog_view,
                    profile_view=profile_view,
                    record=record,
                ),
                settings=settings,
            )
        if trace.group_id != profile_view.group_id:
            sequence = _append_inconsistency(
                inconsistencies=inconsistencies,
                sequence=sequence,
                inconsistency_type=InconsistencyType.INCOMPLETE_REFERENCE,
                criterion=ConsistencyCriterionType.INFORMATION_INTEGRITY,
                description="Referencia de trazabilidad con group_id distinto al perfil evaluado",
                related_evidence_ids=(record.evidence_id,),
                provider_ids=(record.provider_id,) if record.provider_id else (),
                traceability_ref=_build_inconsistency_traceability(
                    catalog_view=catalog_view,
                    profile_view=profile_view,
                    record=record,
                ),
                settings=settings,
            )
        if not trace.document_id:
            sequence = _append_inconsistency(
                inconsistencies=inconsistencies,
                sequence=sequence,
                inconsistency_type=InconsistencyType.INCOMPLETE_REFERENCE,
                criterion=ConsistencyCriterionType.INFORMATION_INTEGRITY,
                description="Evidencia sin document_id en referencia de trazabilidad",
                related_evidence_ids=(record.evidence_id,),
                provider_ids=(record.provider_id,) if record.provider_id else (),
                traceability_ref=_build_inconsistency_traceability(
                    catalog_view=catalog_view,
                    profile_view=profile_view,
                    record=record,
                ),
                settings=settings,
            )
    return sequence


def evaluate_commercial_technical_coherence(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    inconsistencies: list[InconsistencyRecord],
    sequence: int,
    settings: ConsistencyEvaluationEngineSettings,
) -> int:
    if not settings.detect_commercial_technical_contradictions:
        return sequence

    commercial_by_provider: dict[str | None, dict[str, EvidenceRecordView]] = {}
    technical_by_provider: dict[str | None, dict[str, EvidenceRecordView]] = {}

    for record in profile_view.evidence_records:
        if record.evidence_category in _COMMERCIAL_CATEGORIES:
            bucket = commercial_by_provider.setdefault(record.provider_id, {})
            bucket[_normalize_key(record.evidence_key)] = record
        elif record.evidence_category in _TECHNICAL_CATEGORIES:
            bucket = technical_by_provider.setdefault(record.provider_id, {})
            bucket[_normalize_key(record.evidence_key)] = record

    all_providers = set(commercial_by_provider) | set(technical_by_provider)
    for provider_id in all_providers:
        commercial_keys = commercial_by_provider.get(provider_id, {})
        technical_keys = technical_by_provider.get(provider_id, {})
        shared_keys = set(commercial_keys) & set(technical_keys)
        for key in shared_keys:
            commercial_record = commercial_keys[key]
            technical_record = technical_keys[key]
            if str(commercial_record.evidence_value) != str(technical_record.evidence_value):
                sequence = _append_inconsistency(
                    inconsistencies=inconsistencies,
                    sequence=sequence,
                    inconsistency_type=InconsistencyType.CONTRADICTORY_INFORMATION,
                    criterion=ConsistencyCriterionType.COMMERCIAL_TECHNICAL_COHERENCE,
                    description=(
                        f"Valor comercial y técnico distinto para el atributo '{key}'"
                    ),
                    related_evidence_ids=(
                        commercial_record.evidence_id,
                        technical_record.evidence_id,
                    ),
                    provider_ids=(provider_id,) if provider_id else (),
                    traceability_ref=_build_inconsistency_traceability(
                        catalog_view=catalog_view,
                        profile_view=profile_view,
                        record=commercial_record,
                    ),
                    settings=settings,
                    metadata={"evidence_key": key},
                )
    return sequence


def evaluate_provider_comparability(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    inconsistencies: list[InconsistencyRecord],
    sequence: int,
    settings: ConsistencyEvaluationEngineSettings,
) -> int:
    if not settings.detect_provider_attribute_differences:
        return sequence

    provider_records = [
        record
        for record in profile_view.evidence_records
        if record.provider_id is not None
        and record.evidence_category
        in (
            EvidenceCategory.COMMERCIAL_INFORMATION,
            EvidenceCategory.TECHNICAL_INFORMATION,
            EvidenceCategory.COMMERCIAL_CONDITIONS,
        )
    ]
    if len({record.provider_id for record in provider_records}) < 2:
        return sequence

    keys_by_provider: dict[str, set[str]] = {}
    records_by_provider_key: dict[str, dict[str, list[EvidenceRecordView]]] = {}
    for record in provider_records:
        provider_id = str(record.provider_id)
        key = _normalize_key(record.evidence_key)
        keys_by_provider.setdefault(provider_id, set()).add(key)
        records_by_provider_key.setdefault(provider_id, {}).setdefault(key, []).append(record)

    all_keys: set[str] = set()
    for keys in keys_by_provider.values():
        all_keys |= keys

    for key in sorted(all_keys):
        providers_with_key = [
            provider_id for provider_id, keys in keys_by_provider.items() if key in keys
        ]
        providers_without_key = [
            provider_id for provider_id, keys in keys_by_provider.items() if key not in keys
        ]
        if providers_with_key and providers_without_key:
            related_ids = tuple(
                record.evidence_id
                for provider_id in providers_with_key
                for record in records_by_provider_key[provider_id][key]
            )
            sequence = _append_inconsistency(
                inconsistencies=inconsistencies,
                sequence=sequence,
                inconsistency_type=InconsistencyType.RELEVANT_DIFFERENCE,
                criterion=ConsistencyCriterionType.PROVIDER_COMPARABILITY,
                description=(
                    f"Atributo comparable '{key}' presente en algunos proveedores "
                    f"y ausente en otros del mismo Grupo Comparable"
                ),
                related_evidence_ids=related_ids,
                provider_ids=tuple(sorted(providers_with_key + providers_without_key)),
                traceability_ref=_build_inconsistency_traceability(
                    catalog_view=catalog_view,
                    profile_view=profile_view,
                    provider_id=providers_with_key[0],
                ),
                settings=settings,
                metadata={"evidence_key": key},
            )
    return sequence


def evaluate_comparable_attribute_relations(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    inconsistencies: list[InconsistencyRecord],
    sequence: int,
    settings: ConsistencyEvaluationEngineSettings,
) -> int:
    if not settings.detect_incomplete_references:
        return sequence

    column_keys = {
        _normalize_key(record.evidence_key)
        for record in profile_view.evidence_records
        if record.metadata.get("column_id") is not None
        or str(record.traceability_ref.source_field).startswith("dynamic_columns")
    }
    if not column_keys:
        return sequence

    provider_keys = {
        _normalize_key(record.evidence_key)
        for record in profile_view.evidence_records
        if record.provider_id is not None
    }

    for column_key in sorted(column_keys):
        if column_key not in provider_keys:
            column_records = [
                record
                for record in profile_view.evidence_records
                if _normalize_key(record.evidence_key) == column_key
            ]
            if not column_records:
                continue
            sequence = _append_inconsistency(
                inconsistencies=inconsistencies,
                sequence=sequence,
                inconsistency_type=InconsistencyType.INCONSISTENT_ATTRIBUTES,
                criterion=ConsistencyCriterionType.COMPARABLE_ATTRIBUTE_RELATIONS,
                description=(
                    f"Atributo comparable '{column_key}' definido sin valores "
                    f"asociados en proveedores del Grupo Comparable"
                ),
                related_evidence_ids=tuple(record.evidence_id for record in column_records),
                provider_ids=(),
                traceability_ref=_build_inconsistency_traceability(
                    catalog_view=catalog_view,
                    profile_view=profile_view,
                    record=column_records[0],
                ),
                settings=settings,
                metadata={"evidence_key": column_key},
            )
    return sequence


def evaluate_evidence_non_contradiction(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    inconsistencies: list[InconsistencyRecord],
    sequence: int,
    settings: ConsistencyEvaluationEngineSettings,
) -> int:
    if not settings.detect_contradictions:
        return sequence

    grouped = _records_by_provider_and_key(profile_view.evidence_records)
    for provider_id, keys in grouped.items():
        for key, records in keys.items():
            if len(records) < 2:
                continue
            values = {str(record.evidence_value) for record in records}
            categories = {record.evidence_category for record in records}
            if len(values) > 1 and len(categories) == 1:
                sequence = _append_inconsistency(
                    inconsistencies=inconsistencies,
                    sequence=sequence,
                    inconsistency_type=InconsistencyType.CONTRADICTORY_INFORMATION,
                    criterion=ConsistencyCriterionType.EVIDENCE_NON_CONTRADICTION,
                    description=(
                        f"Valores contradictorios para el atributo '{key}' "
                        f"dentro de la misma categoría"
                    ),
                    related_evidence_ids=tuple(record.evidence_id for record in records),
                    provider_ids=(provider_id,) if provider_id else (),
                    traceability_ref=_build_inconsistency_traceability(
                        catalog_view=catalog_view,
                        profile_view=profile_view,
                        record=records[0],
                    ),
                    settings=settings,
                    metadata={"evidence_key": key},
                )
            elif len(values) > 1 and len(categories) > 1:
                sequence = _append_inconsistency(
                    inconsistencies=inconsistencies,
                    sequence=sequence,
                    inconsistency_type=InconsistencyType.INCOMPATIBLE_DATA,
                    criterion=ConsistencyCriterionType.EVIDENCE_NON_CONTRADICTION,
                    description=(
                        f"Datos incompatibles para el atributo '{key}' entre categorías de evidencia"
                    ),
                    related_evidence_ids=tuple(record.evidence_id for record in records),
                    provider_ids=(provider_id,) if provider_id else (),
                    traceability_ref=_build_inconsistency_traceability(
                        catalog_view=catalog_view,
                        profile_view=profile_view,
                        record=records[0],
                    ),
                    settings=settings,
                    metadata={"evidence_key": key},
                )
    return sequence


def assess_sufficiency(
    *,
    profile_view: ModelEvidenceProfileView,
    inconsistencies: tuple[InconsistencyRecord, ...],
    settings: ConsistencyEvaluationEngineSettings,
) -> SufficiencyAssessment:
    evidence_count = len(profile_view.evidence_records)
    missing_count = len(profile_view.missing_evidence_records)
    inconsistency_count = len(inconsistencies)
    blocking_factors: list[str] = []

    contradictory_count = sum(
        1
        for item in inconsistencies
        if item.inconsistency_type == InconsistencyType.CONTRADICTORY_INFORMATION
    )

    if evidence_count == 0:
        blocking_factors.append("sin_evidencias_disponibles")
        return SufficiencyAssessment(
            definitive_model_id=profile_view.definitive_model_id,
            group_id=profile_view.group_id,
            sufficiency_level=SufficiencyLevel.INSUFFICIENT,
            sufficient_for_reasoning=False,
            reason="No hay evidencias disponibles para continuar el razonamiento",
            missing_evidence_count=missing_count,
            inconsistency_count=inconsistency_count,
            blocking_factors=tuple(blocking_factors),
        )

    if contradictory_count > 0 and settings.block_on_contradictions:
        blocking_factors.append("contradicciones_detectadas")

    if missing_count > settings.max_missing_evidence_for_sufficiency:
        blocking_factors.append("informacion_faltante_excesiva")

    if inconsistency_count > settings.max_inconsistencies_for_sufficiency:
        blocking_factors.append("inconsistencias_excesivas")

    if blocking_factors:
        level = (
            SufficiencyLevel.INSUFFICIENT
            if "sin_evidencias_disponibles" in blocking_factors
            or contradictory_count > 0
            else SufficiencyLevel.PARTIAL
        )
        return SufficiencyAssessment(
            definitive_model_id=profile_view.definitive_model_id,
            group_id=profile_view.group_id,
            sufficiency_level=level,
            sufficient_for_reasoning=level == SufficiencyLevel.PARTIAL,
            reason="Evidencias con factores limitantes para el razonamiento posterior",
            missing_evidence_count=missing_count,
            inconsistency_count=inconsistency_count,
            blocking_factors=tuple(blocking_factors),
        )

    if missing_count > 0 or inconsistency_count > 0:
        return SufficiencyAssessment(
            definitive_model_id=profile_view.definitive_model_id,
            group_id=profile_view.group_id,
            sufficiency_level=SufficiencyLevel.PARTIAL,
            sufficient_for_reasoning=True,
            reason="Evidencias suficientes con observaciones de consistencia registradas",
            missing_evidence_count=missing_count,
            inconsistency_count=inconsistency_count,
            blocking_factors=(),
        )

    return SufficiencyAssessment(
        definitive_model_id=profile_view.definitive_model_id,
        group_id=profile_view.group_id,
        sufficiency_level=SufficiencyLevel.SUFFICIENT,
        sufficient_for_reasoning=True,
        reason="Evidencias suficientes para continuar el razonamiento",
        missing_evidence_count=missing_count,
        inconsistency_count=inconsistency_count,
        blocking_factors=(),
    )


def evaluate_profile_consistency(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profile_view: ModelEvidenceProfileView,
    settings: ConsistencyEvaluationEngineSettings,
    start_sequence: int,
) -> tuple[ModelConsistencyProfile, int]:
    inconsistencies: list[InconsistencyRecord] = []
    sequence = start_sequence
    criteria_evaluated: list[str] = []

    if settings.detect_integrity_violations:
        criteria_evaluated.append(ConsistencyCriterionType.INFORMATION_INTEGRITY.value)
        sequence = evaluate_information_integrity(
            catalog_view=catalog_view,
            profile_view=profile_view,
            inconsistencies=inconsistencies,
            sequence=sequence,
            settings=settings,
        )

    if settings.detect_commercial_technical_contradictions:
        criteria_evaluated.append(ConsistencyCriterionType.COMMERCIAL_TECHNICAL_COHERENCE.value)
        sequence = evaluate_commercial_technical_coherence(
            catalog_view=catalog_view,
            profile_view=profile_view,
            inconsistencies=inconsistencies,
            sequence=sequence,
            settings=settings,
        )

    if settings.detect_provider_attribute_differences:
        criteria_evaluated.append(ConsistencyCriterionType.PROVIDER_COMPARABILITY.value)
        sequence = evaluate_provider_comparability(
            catalog_view=catalog_view,
            profile_view=profile_view,
            inconsistencies=inconsistencies,
            sequence=sequence,
            settings=settings,
        )

    if settings.detect_incomplete_references:
        criteria_evaluated.append(ConsistencyCriterionType.COMPARABLE_ATTRIBUTE_RELATIONS.value)
        sequence = evaluate_comparable_attribute_relations(
            catalog_view=catalog_view,
            profile_view=profile_view,
            inconsistencies=inconsistencies,
            sequence=sequence,
            settings=settings,
        )

    if settings.detect_contradictions:
        criteria_evaluated.append(ConsistencyCriterionType.EVIDENCE_NON_CONTRADICTION.value)
        sequence = evaluate_evidence_non_contradiction(
            catalog_view=catalog_view,
            profile_view=profile_view,
            inconsistencies=inconsistencies,
            sequence=sequence,
            settings=settings,
        )

    inconsistency_tuple = tuple(inconsistencies)
    sufficiency = assess_sufficiency(
        profile_view=profile_view,
        inconsistencies=inconsistency_tuple,
        settings=settings,
    )

    profile = ModelConsistencyProfile(
        definitive_model_id=profile_view.definitive_model_id,
        comparative_table_id=profile_view.comparative_table_id,
        group_id=profile_view.group_id,
        group_type=profile_view.group_type,
        inconsistencies=inconsistency_tuple,
        sufficiency=sufficiency,
        criteria_evaluated=tuple(criteria_evaluated),
        evidence_records_evaluated=len(profile_view.evidence_records),
        source_data_preserved=profile_view.source_data_preserved,
    )
    return profile, sequence


def build_consistency_catalog(
    *,
    catalog_view: EvidenceAnalysisCatalogView,
    profiles: tuple[ModelConsistencyProfile, ...],
    settings: ConsistencyEvaluationEngineSettings,
) -> ConsistencyEvaluationCatalog:
    return ConsistencyEvaluationCatalog(
        catalog_id=f"cee-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_evidence_catalog_id=catalog_view.catalog_id,
        profiles=profiles,
        risk_analysis_engine_prepared=settings.risk_analysis_engine_prepared,
        evidence_catalog_preserved=True,
        source_data_preserved=catalog_view.source_data_preserved,
    )
