"""Utilidades de validación del Modelo Comparativo Definitivo."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ValidationFindingCategory,
    ValidationFindingSeverity,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.gateway import (
    DefinitiveCatalogView,
    DefinitiveModelView,
    ModelValidationInputView,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeValidationCheckSet,
    ComparativeValidationFinding,
    ComparativeValidationReport,
    ComparativeValidationTraceability,
)
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeValidationFrameworkSettings,
)


def build_public_finding_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_finding(
    *,
    finding_id: str,
    category: ValidationFindingCategory,
    severity: ValidationFindingSeverity,
    definitive_model_id: str,
    group_id: str,
    message: str,
    validator_name: str,
    metadata: dict | None = None,
) -> ComparativeValidationFinding:
    return ComparativeValidationFinding(
        finding_id=finding_id,
        category=category,
        severity=severity,
        definitive_model_id=definitive_model_id,
        group_id=group_id,
        message=message,
        validator_name=validator_name,
        metadata=metadata or {},
    )


def validate_model_structure(
    *,
    model: DefinitiveModelView,
    validator_name: str,
    sequence: int,
    settings: ComparativeValidationFrameworkSettings,
) -> tuple[list[ComparativeValidationFinding], int]:
    findings: list[ComparativeValidationFinding] = []
    seq = sequence

    if not model.definitive_model_id.strip():
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.STRUCTURAL,
                severity=ValidationFindingSeverity.ERROR,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Modelo definitivo sin identificador válido",
                validator_name=validator_name,
            ),
        )
        seq += 1

    if not model.group_id.strip():
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.STRUCTURAL,
                severity=ValidationFindingSeverity.ERROR,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Modelo definitivo sin Grupo Comparable asociado",
                validator_name=validator_name,
            ),
        )
        seq += 1

    if not model.comparative_table_id.strip():
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.STRUCTURAL,
                severity=ValidationFindingSeverity.ERROR,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Modelo definitivo sin identificador de cuadro comparativo",
                validator_name=validator_name,
            ),
        )
        seq += 1

    return findings, seq


def validate_model_completeness(
    *,
    model: DefinitiveModelView,
    validator_name: str,
    sequence: int,
    settings: ComparativeValidationFrameworkSettings,
) -> tuple[list[ComparativeValidationFinding], int]:
    findings: list[ComparativeValidationFinding] = []
    seq = sequence
    model_dict = {
        "definitive_model_id": model.definitive_model_id,
        "comparative_table_id": model.comparative_table_id,
        "group_id": model.group_id,
        "group_type": model.group_type,
        "dynamic_columns": model.dynamic_columns,
        "dynamic_rows": model.dynamic_rows,
        "provider_organization": model.provider_organization,
        "commercial_information": model.commercial_information,
        "technical_information": model.technical_information,
        "inherited_context": model.inherited_context,
        "confidence_level_available": model.confidence_level_available,
        "metadata": model.metadata,
        "traceability": model.traceability,
        "motor_internal_references": model.motor_internal_references,
    }

    for field in PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS:
        value = model_dict.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.COMPLETENESS,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"Campo obligatorio ausente en modelo definitivo: {field}",
                    validator_name=validator_name,
                    metadata={"missing_field": field},
                ),
            )
            seq += 1
        elif isinstance(value, (list, tuple)) and len(value) == 0:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.COMPLETENESS,
                    severity=ValidationFindingSeverity.WARNING,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"Conjunto vacío en modelo definitivo: {field}",
                    validator_name=validator_name,
                    metadata={"empty_field": field},
                ),
            )
            seq += 1

    return findings, seq


def validate_model_integrity(
    *,
    model: DefinitiveModelView,
    validator_name: str,
    sequence: int,
    settings: ComparativeValidationFrameworkSettings,
) -> tuple[list[ComparativeValidationFinding], int]:
    findings: list[ComparativeValidationFinding] = []
    seq = sequence

    column_ids = {
        str(col.get("column_id", ""))
        for col in model.dynamic_columns
        if col.get("column_id")
    }
    row_ids = {
        str(row.get("row_id", ""))
        for row in model.dynamic_rows
        if row.get("row_id")
    }

    referenced_columns: set[str] = set()
    for row in model.dynamic_rows:
        refs = row.get("column_references", [])
        if isinstance(refs, list):
            for ref in refs:
                ref_str = str(ref)
                referenced_columns.add(ref_str)
                if ref_str not in column_ids:
                    findings.append(
                        build_finding(
                            finding_id=build_public_finding_id(
                                seq,
                                prefix=settings.finding_id_prefix,
                                padding=settings.finding_id_padding,
                            ),
                            category=ValidationFindingCategory.INTEGRITY,
                            severity=ValidationFindingSeverity.ERROR,
                            definitive_model_id=model.definitive_model_id,
                            group_id=model.group_id,
                            message=(
                                f"Fila {row.get('row_id', '')} referencia columna "
                                f"inexistente: {ref_str}"
                            ),
                            validator_name=validator_name,
                            metadata={"row_id": row.get("row_id"), "column_id": ref_str},
                        ),
                    )
                    seq += 1

    orphan_columns = column_ids - referenced_columns
    for column_id in sorted(orphan_columns):
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq,
                    prefix=settings.finding_id_prefix,
                    padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.INTEGRITY,
                severity=ValidationFindingSeverity.WARNING,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message=f"Columna sin referencia en filas: {column_id}",
                validator_name=validator_name,
                metadata={"column_id": column_id},
            ),
        )
        seq += 1

    for provider in model.provider_organization:
        row_ref = str(provider.get("row_id", ""))
        if row_ref and row_ref not in row_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.INTEGRITY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=(
                        f"Proveedor {provider.get('provider_id', '')} referencia fila "
                        f"inexistente: {row_ref}"
                    ),
                    validator_name=validator_name,
                    metadata={"provider_id": provider.get("provider_id"), "row_id": row_ref},
                ),
            )
            seq += 1

        refs = provider.get("column_references", [])
        if isinstance(refs, list):
            for ref in refs:
                ref_str = str(ref)
                if ref_str not in column_ids:
                    findings.append(
                        build_finding(
                            finding_id=build_public_finding_id(
                                seq,
                                prefix=settings.finding_id_prefix,
                                padding=settings.finding_id_padding,
                            ),
                            category=ValidationFindingCategory.INTEGRITY,
                            severity=ValidationFindingSeverity.ERROR,
                            definitive_model_id=model.definitive_model_id,
                            group_id=model.group_id,
                            message=(
                                f"Proveedor {provider.get('provider_id', '')} referencia "
                                f"columna inexistente: {ref_str}"
                            ),
                            validator_name=validator_name,
                            metadata={
                                "provider_id": provider.get("provider_id"),
                                "column_id": ref_str,
                            },
                        ),
                    )
                    seq += 1

    return findings, seq


def validate_model_consistency(
    *,
    model: DefinitiveModelView,
    validator_name: str,
    sequence: int,
    settings: ComparativeValidationFrameworkSettings,
) -> tuple[list[ComparativeValidationFinding], int]:
    findings: list[ComparativeValidationFinding] = []
    seq = sequence

    seen_column_ids: set[str] = set()
    for column in model.dynamic_columns:
        column_id = str(column.get("column_id", ""))
        if column_id in seen_column_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.CONSISTENCY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"Columna duplicada detectada: {column_id}",
                    validator_name=validator_name,
                    metadata={"column_id": column_id},
                ),
            )
            seq += 1
        if column_id:
            seen_column_ids.add(column_id)

    seen_row_ids: set[str] = set()
    for row in model.dynamic_rows:
        row_id = str(row.get("row_id", ""))
        if row_id in seen_row_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.CONSISTENCY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"Fila duplicada detectada: {row_id}",
                    validator_name=validator_name,
                    metadata={"row_id": row_id},
                ),
            )
            seq += 1
        if row_id:
            seen_row_ids.add(row_id)

    seen_providers: set[str] = set()
    for provider in model.provider_organization:
        provider_id = str(provider.get("provider_id", "")).strip().lower()
        if provider_id in seen_providers:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.CONSISTENCY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"Proveedor duplicado detectado: {provider.get('provider_id', '')}",
                    validator_name=validator_name,
                    metadata={"provider_id": provider.get("provider_id")},
                ),
            )
            seq += 1
        if provider_id:
            seen_providers.add(provider_id)

    return findings, seq


def validate_model_traceability(
    *,
    model: DefinitiveModelView,
    validator_name: str,
    sequence: int,
    settings: ComparativeValidationFrameworkSettings,
) -> tuple[list[ComparativeValidationFinding], int]:
    findings: list[ComparativeValidationFinding] = []
    seq = sequence

    if not model.traceability:
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.TRACEABILITY,
                severity=ValidationFindingSeverity.ERROR,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Modelo definitivo sin trazabilidad documental",
                validator_name=validator_name,
            ),
        )
        seq += 1

    document_evidence = model.traceability.get("document_evidence", {})
    if isinstance(document_evidence, dict) and not document_evidence.get("document_id"):
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.TRACEABILITY,
                severity=ValidationFindingSeverity.ERROR,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Trazabilidad sin referencia al documento de origen",
                validator_name=validator_name,
            ),
        )
        seq += 1

    comparable_group = model.traceability.get("comparable_group", {})
    if isinstance(comparable_group, dict) and not comparable_group.get("group_id"):
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.TRACEABILITY,
                severity=ValidationFindingSeverity.WARNING,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Trazabilidad sin referencia explícita al Grupo Comparable",
                validator_name=validator_name,
            ),
        )
        seq += 1

    required_refs = (
        "enriched_catalog_id",
        "structure_catalog_id",
        "integrity_report_id",
    )
    for ref_key in required_refs:
        if not model.motor_internal_references.get(ref_key, "").strip():
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.TRACEABILITY,
                    severity=ValidationFindingSeverity.WARNING,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"Referencia interna del Motor ausente: {ref_key}",
                    validator_name=validator_name,
                    metadata={"missing_reference": ref_key},
                ),
            )
            seq += 1

    if not isinstance(model.inherited_context, dict):
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=ValidationFindingCategory.TRACEABILITY,
                severity=ValidationFindingSeverity.ERROR,
                definitive_model_id=model.definitive_model_id,
                group_id=model.group_id,
                message="Contexto heredado con formato inválido",
                validator_name=validator_name,
            ),
        )
        seq += 1

    return findings, seq


def build_check_set(
    *,
    model: DefinitiveModelView,
    findings: tuple[ComparativeValidationFinding, ...],
) -> ComparativeValidationCheckSet:
    has_errors = any(
        finding.severity == ValidationFindingSeverity.ERROR for finding in findings
    )
    return ComparativeValidationCheckSet(
        definitive_model_id=model.definitive_model_id,
        group_id=model.group_id,
        comparative_table_id=model.comparative_table_id,
        findings=findings,
        is_valid=not has_errors,
    )


def build_global_consistency_findings(
    *,
    catalog: DefinitiveCatalogView,
    validator_name: str,
    sequence: int,
    settings: ComparativeValidationFrameworkSettings,
) -> tuple[list[ComparativeValidationFinding], int]:
    findings: list[ComparativeValidationFinding] = []
    seq = sequence

    seen_definitive_ids: set[str] = set()
    seen_table_ids: set[str] = set()
    seen_group_ids: set[str] = set()

    for model in catalog.models:
        if model.definitive_model_id in seen_definitive_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.CONSISTENCY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"definitive_model_id duplicado en catálogo: {model.definitive_model_id}",
                    validator_name=validator_name,
                ),
            )
            seq += 1
        seen_definitive_ids.add(model.definitive_model_id)

        if model.comparative_table_id in seen_table_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.CONSISTENCY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=(
                        f"comparative_table_id duplicado en catálogo: "
                        f"{model.comparative_table_id}"
                    ),
                    validator_name=validator_name,
                ),
            )
            seq += 1
        seen_table_ids.add(model.comparative_table_id)

        if model.group_id in seen_group_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq,
                        prefix=settings.finding_id_prefix,
                        padding=settings.finding_id_padding,
                    ),
                    category=ValidationFindingCategory.CONSISTENCY,
                    severity=ValidationFindingSeverity.ERROR,
                    definitive_model_id=model.definitive_model_id,
                    group_id=model.group_id,
                    message=f"group_id duplicado en catálogo: {model.group_id}",
                    validator_name=validator_name,
                ),
            )
            seq += 1
        seen_group_ids.add(model.group_id)

    return findings, seq


def build_validation_report(
    *,
    input_view: ModelValidationInputView,
    check_sets: tuple[ComparativeValidationCheckSet, ...],
    global_findings: tuple[ComparativeValidationFinding, ...],
    comparative_quality_framework_prepared: bool,
) -> ComparativeValidationReport:
    catalog = input_view.definitive_catalog
    traceability = ComparativeValidationTraceability(
        process_id=catalog.process_id,
        document_id=catalog.document_id,
        model_id=catalog.model_id,
        source_definitive_catalog_id=catalog.catalog_id,
        definitive_catalog_preserved=True,
        domain_model_preserved=catalog.domain_model_preserved,
    )
    return ComparativeValidationReport(
        report_id=f"cvf-report://{catalog.model_id}",
        process_id=catalog.process_id,
        model_id=catalog.model_id,
        document_id=catalog.document_id,
        source_definitive_catalog_id=catalog.catalog_id,
        check_sets=check_sets,
        global_findings=global_findings,
        traceability=traceability,
        comparative_quality_framework_prepared=comparative_quality_framework_prepared,
        definitive_catalog_preserved=True,
        domain_model_preserved=catalog.domain_model_preserved,
    )
