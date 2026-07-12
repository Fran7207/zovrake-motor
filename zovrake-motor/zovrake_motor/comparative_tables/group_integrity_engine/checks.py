"""Utilidades de validación de integridad estructural."""

from __future__ import annotations

from zovrake_motor.comparative_tables.group_integrity_engine.enums import (
    IntegrityFindingCategory,
    IntegrityFindingSeverity,
)
from zovrake_motor.comparative_tables.group_integrity_engine.gateway import (
    ColumnSetView,
    IntegrityValidationInputView,
    ProviderSetView,
    RowSetView,
    StructureView,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityCheckSet,
    GroupIntegrityFinding,
    GroupIntegrityReport,
    GroupIntegrityTraceability,
)
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings


def build_public_finding_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_finding(
    *,
    finding_id: str,
    category: IntegrityFindingCategory,
    severity: IntegrityFindingSeverity,
    group_id: str,
    table_id: str,
    message: str,
    validator_name: str,
    metadata: dict | None = None,
) -> GroupIntegrityFinding:
    return GroupIntegrityFinding(
        finding_id=finding_id,
        category=category,
        severity=severity,
        group_id=group_id,
        table_id=table_id,
        message=message,
        validator_name=validator_name,
        metadata=metadata or {},
    )


def validate_group_structure(
    *,
    structure: StructureView,
    validator_name: str,
    sequence: int,
    settings: GroupIntegrityEngineSettings,
) -> tuple[list[GroupIntegrityFinding], int]:
    findings: list[GroupIntegrityFinding] = []
    seq = sequence

    if not structure.group_id.strip():
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=IntegrityFindingCategory.GROUP,
                severity=IntegrityFindingSeverity.ERROR,
                group_id=structure.group_id,
                table_id=structure.table_id,
                message="Grupo Comparable sin identificador válido",
                validator_name=validator_name,
            ),
        )
        seq += 1

    if not structure.comparative_model_id.strip():
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=IntegrityFindingCategory.GROUP,
                severity=IntegrityFindingSeverity.ERROR,
                group_id=structure.group_id,
                table_id=structure.table_id,
                message="Grupo Comparable sin relación con el Modelo Comparativo de Dominio",
                validator_name=validator_name,
            ),
        )
        seq += 1

    if not structure.domain_catalog_id.strip():
        findings.append(
            build_finding(
                finding_id=build_public_finding_id(
                    seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                ),
                category=IntegrityFindingCategory.GROUP,
                severity=IntegrityFindingSeverity.WARNING,
                group_id=structure.group_id,
                table_id=structure.table_id,
                message="Referencia al catálogo de dominio ausente en la estructura",
                validator_name=validator_name,
            ),
        )
        seq += 1

    return findings, seq


def validate_columns_for_set(
    *,
    column_set: ColumnSetView,
    validator_name: str,
    sequence: int,
    settings: GroupIntegrityEngineSettings,
) -> tuple[list[GroupIntegrityFinding], int]:
    findings: list[GroupIntegrityFinding] = []
    seq = sequence
    seen_ids: set[str] = set()

    for column in column_set.columns:
        if column.column_id in seen_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.COLUMN,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=column_set.group_id,
                    table_id=column_set.table_id,
                    message=f"Columna duplicada detectada: {column.column_id}",
                    validator_name=validator_name,
                    metadata={"column_id": column.column_id},
                ),
            )
            seq += 1
        seen_ids.add(column.column_id)

        if column.group_id != column_set.group_id:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.COLUMN,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=column_set.group_id,
                    table_id=column_set.table_id,
                    message=(
                        f"Columna {column.column_id} no pertenece al grupo {column_set.group_id}"
                    ),
                    validator_name=validator_name,
                    metadata={"column_id": column.column_id, "column_group_id": column.group_id},
                ),
            )
            seq += 1

    return findings, seq


def validate_rows_for_set(
    *,
    row_set: RowSetView,
    column_ids: set[str],
    validator_name: str,
    sequence: int,
    settings: GroupIntegrityEngineSettings,
) -> tuple[list[GroupIntegrityFinding], int]:
    findings: list[GroupIntegrityFinding] = []
    seq = sequence
    seen_ids: set[str] = set()

    for row in row_set.rows:
        if row.row_id in seen_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.ROW,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=row_set.group_id,
                    table_id=row_set.table_id,
                    message=f"Fila duplicada detectada: {row.row_id}",
                    validator_name=validator_name,
                    metadata={"row_id": row.row_id},
                ),
            )
            seq += 1
        seen_ids.add(row.row_id)

        if row.group_id != row_set.group_id:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.ROW,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=row_set.group_id,
                    table_id=row_set.table_id,
                    message=f"Fila {row.row_id} no pertenece al grupo {row_set.group_id}",
                    validator_name=validator_name,
                    metadata={"row_id": row.row_id, "row_group_id": row.group_id},
                ),
            )
            seq += 1

        for column_ref in row.column_references:
            if column_ref not in column_ids:
                findings.append(
                    build_finding(
                        finding_id=build_public_finding_id(
                            seq,
                            prefix=settings.finding_id_prefix,
                            padding=settings.finding_id_padding,
                        ),
                        category=IntegrityFindingCategory.ROW,
                        severity=IntegrityFindingSeverity.ERROR,
                        group_id=row_set.group_id,
                        table_id=row_set.table_id,
                        message=(
                            f"Fila {row.row_id} referencia columna inexistente: {column_ref}"
                        ),
                        validator_name=validator_name,
                        metadata={"row_id": row.row_id, "column_id": column_ref},
                    ),
                )
                seq += 1

    return findings, seq


def validate_providers_for_set(
    *,
    provider_set: ProviderSetView,
    row_ids: set[str],
    column_ids: set[str],
    validator_name: str,
    sequence: int,
    settings: GroupIntegrityEngineSettings,
) -> tuple[list[GroupIntegrityFinding], int]:
    findings: list[GroupIntegrityFinding] = []
    seq = sequence
    seen_providers: set[str] = set()
    seen_org_ids: set[str] = set()

    for provider in provider_set.providers:
        normalized = provider.provider_id.strip().lower()
        if normalized in seen_providers:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.PROVIDER,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=provider_set.group_id,
                    table_id=provider_set.table_id,
                    message=f"Proveedor duplicado detectado: {provider.provider_id}",
                    validator_name=validator_name,
                    metadata={"provider_id": provider.provider_id},
                ),
            )
            seq += 1
        seen_providers.add(normalized)

        if provider.organization_id in seen_org_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.PROVIDER,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=provider_set.group_id,
                    table_id=provider_set.table_id,
                    message=(
                        f"organization_id duplicado detectado: {provider.organization_id}"
                    ),
                    validator_name=validator_name,
                    metadata={"organization_id": provider.organization_id},
                ),
            )
            seq += 1
        if provider.organization_id:
            seen_org_ids.add(provider.organization_id)

        if provider.group_id != provider_set.group_id:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.PROVIDER,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=provider_set.group_id,
                    table_id=provider_set.table_id,
                    message=(
                        f"Proveedor {provider.provider_id} no pertenece al grupo "
                        f"{provider_set.group_id}"
                    ),
                    validator_name=validator_name,
                    metadata={"provider_id": provider.provider_id},
                ),
            )
            seq += 1

        if provider.row_id not in row_ids:
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.PROVIDER,
                    severity=IntegrityFindingSeverity.ERROR,
                    group_id=provider_set.group_id,
                    table_id=provider_set.table_id,
                    message=(
                        f"Proveedor {provider.provider_id} referencia fila inexistente: "
                        f"{provider.row_id}"
                    ),
                    validator_name=validator_name,
                    metadata={"provider_id": provider.provider_id, "row_id": provider.row_id},
                ),
            )
            seq += 1

        if not provider.document_reference.strip():
            findings.append(
                build_finding(
                    finding_id=build_public_finding_id(
                        seq, prefix=settings.finding_id_prefix, padding=settings.finding_id_padding,
                    ),
                    category=IntegrityFindingCategory.PROVIDER,
                    severity=IntegrityFindingSeverity.WARNING,
                    group_id=provider_set.group_id,
                    table_id=provider_set.table_id,
                    message=(
                        f"Proveedor {provider.provider_id} sin referencia documental válida"
                    ),
                    validator_name=validator_name,
                    metadata={"provider_id": provider.provider_id},
                ),
            )
            seq += 1

        for column_ref in provider.column_references:
            if column_ref not in column_ids:
                findings.append(
                    build_finding(
                        finding_id=build_public_finding_id(
                            seq,
                            prefix=settings.finding_id_prefix,
                            padding=settings.finding_id_padding,
                        ),
                        category=IntegrityFindingCategory.PROVIDER,
                        severity=IntegrityFindingSeverity.ERROR,
                        group_id=provider_set.group_id,
                        table_id=provider_set.table_id,
                        message=(
                            f"Proveedor {provider.provider_id} referencia columna inexistente: "
                            f"{column_ref}"
                        ),
                        validator_name=validator_name,
                        metadata={"provider_id": provider.provider_id, "column_id": column_ref},
                    ),
                )
                seq += 1

    return findings, seq


def build_check_set(
    *,
    table_id: str,
    group_id: str,
    findings: tuple[GroupIntegrityFinding, ...],
) -> GroupIntegrityCheckSet:
    has_errors = any(
        finding.severity == IntegrityFindingSeverity.ERROR for finding in findings
    )
    return GroupIntegrityCheckSet(
        table_id=table_id,
        group_id=group_id,
        findings=findings,
        is_valid=not has_errors,
    )


def build_integrity_report(
    *,
    input_view: IntegrityValidationInputView,
    check_sets: tuple[GroupIntegrityCheckSet, ...],
    global_findings: tuple[GroupIntegrityFinding, ...],
    traceability_metadata_engine_prepared: bool,
) -> GroupIntegrityReport:
    traceability = GroupIntegrityTraceability(
        process_id=input_view.provider_catalog.process_id,
        document_id=input_view.provider_catalog.document_id,
        model_id=input_view.provider_catalog.model_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        source_provider_catalog_id=input_view.provider_catalog.catalog_id,
        structure_catalog_preserved=True,
        column_catalog_preserved=True,
        row_catalog_preserved=True,
        provider_catalog_preserved=True,
        domain_model_preserved=input_view.provider_catalog.domain_model_preserved,
    )
    return GroupIntegrityReport(
        report_id=f"gie-report://{input_view.provider_catalog.model_id}",
        process_id=input_view.provider_catalog.process_id,
        model_id=input_view.provider_catalog.model_id,
        document_id=input_view.provider_catalog.document_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        source_provider_catalog_id=input_view.provider_catalog.catalog_id,
        check_sets=check_sets,
        global_findings=global_findings,
        traceability=traceability,
        traceability_metadata_engine_prepared=traceability_metadata_engine_prepared,
        structure_catalog_preserved=True,
        column_catalog_preserved=True,
        row_catalog_preserved=True,
        provider_catalog_preserved=True,
        domain_model_preserved=input_view.provider_catalog.domain_model_preserved,
    )
