"""Utilidades de identificación y organización de evidencias."""

from __future__ import annotations

from typing import Any

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import (
    EvidenceCategory,
    EvidencePresenceStatus,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.gateway import (
    DefinitiveComparativeModelCatalogView,
    DefinitiveComparativeModelView,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.governance import (
    EXPECTED_EVIDENCE_CATEGORIES,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisCatalog,
    EvidenceRecord,
    EvidenceTraceabilityReference,
    MissingEvidenceRecord,
    ModelEvidenceProfile,
)
from zovrake_motor.config.categories.intelligent_analysis import EvidenceAnalysisEngineSettings

_DELIVERY_KEYWORDS = ("entrega", "delivery", "plazo", "tiempo", "lead_time")
_WARRANTY_KEYWORDS = ("garantia", "garantía", "warranty", "garant")
_CERTIFICATION_KEYWORDS = ("certificacion", "certificación", "certification", "iso", "norma")
_OBSERVATION_KEYWORDS = ("observacion", "observación", "observation", "nota", "comentario")
_RESTRICTION_KEYWORDS = ("restriccion", "restricción", "restriction", "exclusion", "limite", "límite")
_CONDITION_KEYWORDS = (
    "condicion",
    "condición",
    "condition",
    "pago",
    "payment",
    "moneda",
    "currency",
    "precio",
    "price",
    "total",
)


def build_public_evidence_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_public_missing_evidence_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-MISS-{sequence:0{padding}d}"


def _normalize_key(value: str) -> str:
    return str(value).strip().lower()


def classify_evidence_category(*, key: str, source_field: str) -> EvidenceCategory:
    normalized_key = _normalize_key(key)
    normalized_source = _normalize_key(source_field)

    if normalized_source in {"inherited_context", "requirement_context"}:
        return EvidenceCategory.REQUIREMENT_CONTEXT

    if normalized_source in {"metadata", "motor_internal_references", "model_metadata"}:
        return EvidenceCategory.METADATA

    if any(keyword in normalized_key for keyword in _DELIVERY_KEYWORDS):
        return EvidenceCategory.DELIVERY_TIMES
    if any(keyword in normalized_key for keyword in _WARRANTY_KEYWORDS):
        return EvidenceCategory.WARRANTIES
    if any(keyword in normalized_key for keyword in _CERTIFICATION_KEYWORDS):
        return EvidenceCategory.CERTIFICATIONS
    if any(keyword in normalized_key for keyword in _OBSERVATION_KEYWORDS):
        return EvidenceCategory.OBSERVATIONS
    if any(keyword in normalized_key for keyword in _RESTRICTION_KEYWORDS):
        return EvidenceCategory.RESTRICTIONS
    if any(keyword in normalized_key for keyword in _CONDITION_KEYWORDS):
        return EvidenceCategory.COMMERCIAL_CONDITIONS

    if normalized_source in {"technical_information", "technical_information.fields", "technical_information.specifications"}:
        return EvidenceCategory.TECHNICAL_INFORMATION
    if normalized_source in {"commercial_information", "commercial_information.fields"}:
        return EvidenceCategory.COMMERCIAL_INFORMATION
    if normalized_source.startswith("dynamic_columns") and "technical" in normalized_key:
        return EvidenceCategory.TECHNICAL_INFORMATION
    if normalized_source.startswith("dynamic_columns"):
        return EvidenceCategory.COMMERCIAL_INFORMATION
    if normalized_source.startswith("provider_organization"):
        if "technical" in normalized_source:
            return EvidenceCategory.TECHNICAL_INFORMATION
        return EvidenceCategory.COMMERCIAL_INFORMATION

    return EvidenceCategory.METADATA


def build_traceability_reference(
    *,
    catalog_view: DefinitiveComparativeModelCatalogView,
    model_view: DefinitiveComparativeModelView,
    source_field: str,
    provider_id: str | None = None,
) -> EvidenceTraceabilityReference:
    traceability = dict(model_view.traceability)
    if provider_id:
        traceability = {
            **traceability,
            "provider_id": provider_id,
        }
    return EvidenceTraceabilityReference(
        document_id=catalog_view.document_id,
        definitive_model_id=model_view.definitive_model_id,
        group_id=model_view.group_id,
        comparative_table_id=model_view.comparative_table_id,
        provider_id=provider_id,
        source_field=source_field,
        traceability=traceability,
    )


def _append_field_evidence(
    *,
    records: list[EvidenceRecord],
    sequence: int,
    catalog_view: DefinitiveComparativeModelCatalogView,
    model_view: DefinitiveComparativeModelView,
    source_field: str,
    fields: dict[str, Any],
    provider_id: str | None,
    settings: EvidenceAnalysisEngineSettings,
) -> int:
    for key, value in sorted(fields.items()):
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        sequence += 1
        records.append(
            EvidenceRecord(
                evidence_id=build_public_evidence_id(
                    sequence,
                    prefix=settings.evidence_id_prefix,
                    padding=settings.evidence_id_padding,
                ),
                evidence_category=classify_evidence_category(key=str(key), source_field=source_field),
                evidence_key=str(key),
                evidence_value=value,
                presence_status=EvidencePresenceStatus.PRESENT,
                provider_id=provider_id,
                traceability_ref=build_traceability_reference(
                    catalog_view=catalog_view,
                    model_view=model_view,
                    source_field=source_field,
                    provider_id=provider_id,
                ),
                metadata={"source_field": source_field},
            ),
        )
    return sequence


def collect_model_evidence(
    *,
    catalog_view: DefinitiveComparativeModelCatalogView,
    model_view: DefinitiveComparativeModelView,
    settings: EvidenceAnalysisEngineSettings,
    start_sequence: int,
) -> tuple[list[EvidenceRecord], list[MissingEvidenceRecord], int]:
    records: list[EvidenceRecord] = []
    missing_records: list[MissingEvidenceRecord] = []
    sequence = start_sequence

    commercial_fields = dict(model_view.commercial_information.get("fields", {}))
    sequence = _append_field_evidence(
        records=records,
        sequence=sequence,
        catalog_view=catalog_view,
        model_view=model_view,
        source_field="commercial_information.fields",
        fields=commercial_fields,
        provider_id=None,
        settings=settings,
    )

    technical_fields = dict(model_view.technical_information.get("fields", {}))
    sequence = _append_field_evidence(
        records=records,
        sequence=sequence,
        catalog_view=catalog_view,
        model_view=model_view,
        source_field="technical_information.fields",
        fields=technical_fields,
        provider_id=None,
        settings=settings,
    )

    specifications = model_view.technical_information.get("specifications", [])
    if isinstance(specifications, list):
        for specification in specifications:
            if not str(specification).strip():
                continue
            sequence += 1
            records.append(
                EvidenceRecord(
                    evidence_id=build_public_evidence_id(
                        sequence,
                        prefix=settings.evidence_id_prefix,
                        padding=settings.evidence_id_padding,
                    ),
                    evidence_category=EvidenceCategory.TECHNICAL_INFORMATION,
                    evidence_key=str(specification),
                    evidence_value=specification,
                    presence_status=EvidencePresenceStatus.PRESENT,
                    provider_id=None,
                    traceability_ref=build_traceability_reference(
                        catalog_view=catalog_view,
                        model_view=model_view,
                        source_field="technical_information.specifications",
                    ),
                    metadata={"source_field": "technical_information.specifications"},
                ),
            )

    if model_view.inherited_context:
        sequence = _append_field_evidence(
            records=records,
            sequence=sequence,
            catalog_view=catalog_view,
            model_view=model_view,
            source_field="inherited_context",
            fields=model_view.inherited_context,
            provider_id=None,
            settings=settings,
        )

    if model_view.metadata:
        sequence = _append_field_evidence(
            records=records,
            sequence=sequence,
            catalog_view=catalog_view,
            model_view=model_view,
            source_field="metadata",
            fields=model_view.metadata,
            provider_id=None,
            settings=settings,
        )

    if model_view.motor_internal_references:
        sequence = _append_field_evidence(
            records=records,
            sequence=sequence,
            catalog_view=catalog_view,
            model_view=model_view,
            source_field="motor_internal_references",
            fields=model_view.motor_internal_references,
            provider_id=None,
            settings=settings,
        )

    for column in model_view.dynamic_columns:
        attribute_name = str(column.get("attribute_name", column.get("column_id", "")))
        if not attribute_name.strip():
            continue
        sequence += 1
        records.append(
            EvidenceRecord(
                evidence_id=build_public_evidence_id(
                    sequence,
                    prefix=settings.evidence_id_prefix,
                    padding=settings.evidence_id_padding,
                ),
                evidence_category=classify_evidence_category(
                    key=attribute_name,
                    source_field="dynamic_columns." + str(column.get("attribute_source", "")),
                ),
                evidence_key=attribute_name,
                evidence_value=column.get("metadata", {}),
                presence_status=EvidencePresenceStatus.PRESENT,
                provider_id=None,
                traceability_ref=build_traceability_reference(
                    catalog_view=catalog_view,
                    model_view=model_view,
                    source_field="dynamic_columns",
                ),
                metadata={
                    "column_id": column.get("column_id"),
                    "attribute_source": column.get("attribute_source"),
                },
            ),
        )

    for provider in model_view.provider_organization:
        provider_id = str(provider.get("provider_id", ""))
        provider_commercial = dict(provider.get("commercial_information", {}).get("fields", {}))
        sequence = _append_field_evidence(
            records=records,
            sequence=sequence,
            catalog_view=catalog_view,
            model_view=model_view,
            source_field="provider_organization.commercial_information.fields",
            fields=provider_commercial,
            provider_id=provider_id or None,
            settings=settings,
        )
        provider_technical = dict(provider.get("technical_information", {}).get("fields", {}))
        sequence = _append_field_evidence(
            records=records,
            sequence=sequence,
            catalog_view=catalog_view,
            model_view=model_view,
            source_field="provider_organization.technical_information.fields",
            fields=provider_technical,
            provider_id=provider_id or None,
            settings=settings,
        )
        provider_specs = provider.get("technical_information", {}).get("specifications", [])
        if isinstance(provider_specs, list):
            for specification in provider_specs:
                if not str(specification).strip():
                    continue
                sequence += 1
                records.append(
                    EvidenceRecord(
                        evidence_id=build_public_evidence_id(
                            sequence,
                            prefix=settings.evidence_id_prefix,
                            padding=settings.evidence_id_padding,
                        ),
                        evidence_category=EvidenceCategory.TECHNICAL_INFORMATION,
                        evidence_key=str(specification),
                        evidence_value=specification,
                        presence_status=EvidencePresenceStatus.PRESENT,
                        provider_id=provider_id or None,
                        traceability_ref=build_traceability_reference(
                            catalog_view=catalog_view,
                            model_view=model_view,
                            source_field="provider_organization.technical_information.specifications",
                            provider_id=provider_id or None,
                        ),
                        metadata={"provider_id": provider_id},
                    ),
                )

    if settings.detect_missing_cell_values and model_view.dynamic_columns and model_view.dynamic_rows:
        for row in model_view.dynamic_rows:
            metadata = dict(row.get("metadata", {}))
            if metadata.get("cell_values_prepared") is False:
                missing_sequence = len(missing_records) + 1
                missing_records.append(
                    MissingEvidenceRecord(
                        missing_evidence_id=build_public_missing_evidence_id(
                            missing_sequence,
                            prefix=settings.missing_evidence_id_prefix,
                            padding=settings.missing_evidence_id_padding,
                        ),
                        evidence_category=EvidenceCategory.COMMERCIAL_INFORMATION,
                        expected_key="cell_values",
                        provider_id=str(row.get("provider_id")) or None,
                        definitive_model_id=model_view.definitive_model_id,
                        group_id=model_view.group_id,
                        document_id=catalog_view.document_id,
                        reason="Valores de celda no disponibles en el Modelo Comparativo Definitivo",
                    ),
                )

    categories_present = sorted({record.evidence_category.value for record in records})
    categories_missing = [
        category
        for category in EXPECTED_EVIDENCE_CATEGORIES
        if category not in categories_present and settings.detect_missing_categories
    ]

    for category_value in categories_missing:
        missing_sequence = len(missing_records) + 1
        missing_records.append(
            MissingEvidenceRecord(
                missing_evidence_id=build_public_missing_evidence_id(
                    missing_sequence,
                    prefix=settings.missing_evidence_id_prefix,
                    padding=settings.missing_evidence_id_padding,
                ),
                evidence_category=EvidenceCategory(category_value),
                expected_key=category_value,
                provider_id=None,
                definitive_model_id=model_view.definitive_model_id,
                group_id=model_view.group_id,
                document_id=catalog_view.document_id,
                reason="Categoría de evidencia no presente en el Modelo Comparativo Definitivo",
            ),
        )

    return records, missing_records, sequence


def build_model_evidence_profile(
    *,
    catalog_view: DefinitiveComparativeModelCatalogView,
    model_view: DefinitiveComparativeModelView,
    evidence_records: tuple[EvidenceRecord, ...],
    missing_evidence_records: tuple[MissingEvidenceRecord, ...],
) -> ModelEvidenceProfile:
    categories_present = sorted({record.evidence_category.value for record in evidence_records})
    categories_missing = sorted(
        {record.evidence_category.value for record in missing_evidence_records},
    )
    return ModelEvidenceProfile(
        definitive_model_id=model_view.definitive_model_id,
        comparative_table_id=model_view.comparative_table_id,
        group_id=model_view.group_id,
        group_type=model_view.group_type,
        evidence_records=evidence_records,
        missing_evidence_records=missing_evidence_records,
        categories_present=tuple(categories_present),
        categories_missing=tuple(categories_missing),
        confidence_level_available=model_view.confidence_level_available,
        source_data_preserved=model_view.source_data_preserved,
    )


def build_evidence_catalog(
    *,
    catalog_view: DefinitiveComparativeModelCatalogView,
    profiles: tuple[ModelEvidenceProfile, ...],
    settings: EvidenceAnalysisEngineSettings,
) -> EvidenceAnalysisCatalog:
    return EvidenceAnalysisCatalog(
        catalog_id=f"eae-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_definitive_catalog_id=catalog_view.catalog_id,
        profiles=profiles,
        consistency_evaluation_engine_prepared=settings.consistency_evaluation_engine_prepared,
        definitive_catalog_preserved=True,
        source_data_preserved=catalog_view.source_data_preserved,
    )
