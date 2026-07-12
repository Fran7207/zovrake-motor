"""Validadores especializados del Group Integrity Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.group_integrity_engine.checks import (
    build_check_set,
    build_finding,
    validate_columns_for_set,
    validate_group_structure,
    validate_providers_for_set,
    validate_rows_for_set,
)
from zovrake_motor.comparative_tables.group_integrity_engine.enums import (
    IntegrityFindingCategory,
    IntegrityFindingSeverity,
    IntegrityValidatorStrategyType,
)
from zovrake_motor.comparative_tables.group_integrity_engine.gateway import (
    IntegrityValidationInputView,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityFinding,
    IntegrityValidatorResult,
)
from zovrake_motor.comparative_tables.group_integrity_engine.port import IntegrityValidatorPort
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings


class ComparativeTableIntegrityValidator(IntegrityValidatorPort):
    """
    Valida la integridad estructural completa de cada Cuadro Comparativo.

    Verifica grupos, columnas, filas, proveedores y consistencia general.
    """

    @property
    def validator_name(self) -> str:
        return "comparative_table_integrity_validator"

    @property
    def validator_label(self) -> str:
        return "Validador de Integridad — Cuadro Comparativo Completo"

    @property
    def validator_type(self) -> IntegrityValidatorStrategyType:
        return IntegrityValidatorStrategyType.COMPARATIVE_TABLE

    def validate(
        self,
        input_view: IntegrityValidationInputView,
        *,
        settings: GroupIntegrityEngineSettings,
        start_sequence: int,
    ) -> IntegrityValidatorResult:
        check_sets = []
        global_findings: list[GroupIntegrityFinding] = []
        sequence = start_sequence

        structures_by_table = {
            structure.table_id: structure
            for structure in input_view.structure_catalog.structures
        }
        columns_by_table = {
            column_set.table_id: column_set
            for column_set in input_view.column_catalog.column_sets
        }
        rows_by_table = {
            row_set.table_id: row_set for row_set in input_view.row_catalog.row_sets
        }
        providers_by_table = {
            provider_set.table_id: provider_set
            for provider_set in input_view.provider_catalog.provider_sets
        }

        all_table_ids = (
            set(structures_by_table)
            | set(columns_by_table)
            | set(rows_by_table)
            | set(providers_by_table)
        )

        for table_id in sorted(all_table_ids):
            structure = structures_by_table.get(table_id)
            column_set = columns_by_table.get(table_id)
            row_set = rows_by_table.get(table_id)
            provider_set = providers_by_table.get(table_id)

            group_id = ""
            if structure is not None:
                group_id = structure.group_id
            elif column_set is not None:
                group_id = column_set.group_id
            elif row_set is not None:
                group_id = row_set.group_id
            elif provider_set is not None:
                group_id = provider_set.group_id

            findings: list[GroupIntegrityFinding] = []

            if structure is None:
                findings.append(
                    build_finding(
                        finding_id=f"GIC-TEMP-{table_id}",
                        category=IntegrityFindingCategory.GENERAL,
                        severity=IntegrityFindingSeverity.ERROR,
                        group_id=group_id,
                        table_id=table_id,
                        message=f"Estructura base ausente para table_id={table_id}",
                        validator_name=self.validator_name,
                    ),
                )
            else:
                group_findings, sequence = validate_group_structure(
                    structure=structure,
                    validator_name=self.validator_name,
                    sequence=sequence,
                    settings=settings,
                )
                findings.extend(group_findings)

            if column_set is None:
                findings.append(
                    build_finding(
                        finding_id=f"GIC-TEMP-COL-{table_id}",
                        category=IntegrityFindingCategory.GENERAL,
                        severity=IntegrityFindingSeverity.ERROR,
                        group_id=group_id,
                        table_id=table_id,
                        message=f"Conjunto de columnas ausente para table_id={table_id}",
                        validator_name=self.validator_name,
                    ),
                )
            else:
                column_findings, sequence = validate_columns_for_set(
                    column_set=column_set,
                    validator_name=self.validator_name,
                    sequence=sequence,
                    settings=settings,
                )
                findings.extend(column_findings)

            column_ids = (
                {column.column_id for column in column_set.columns}
                if column_set is not None
                else set()
            )

            if row_set is None:
                findings.append(
                    build_finding(
                        finding_id=f"GIC-TEMP-ROW-{table_id}",
                        category=IntegrityFindingCategory.GENERAL,
                        severity=IntegrityFindingSeverity.ERROR,
                        group_id=group_id,
                        table_id=table_id,
                        message=f"Conjunto de filas ausente para table_id={table_id}",
                        validator_name=self.validator_name,
                    ),
                )
            else:
                row_findings, sequence = validate_rows_for_set(
                    row_set=row_set,
                    column_ids=column_ids,
                    validator_name=self.validator_name,
                    sequence=sequence,
                    settings=settings,
                )
                findings.extend(row_findings)

            row_ids = {row.row_id for row in row_set.rows} if row_set is not None else set()

            if provider_set is None:
                findings.append(
                    build_finding(
                        finding_id=f"GIC-TEMP-PROV-{table_id}",
                        category=IntegrityFindingCategory.GENERAL,
                        severity=IntegrityFindingSeverity.ERROR,
                        group_id=group_id,
                        table_id=table_id,
                        message=f"Conjunto de proveedores ausente para table_id={table_id}",
                        validator_name=self.validator_name,
                    ),
                )
            else:
                provider_findings, sequence = validate_providers_for_set(
                    provider_set=provider_set,
                    row_ids=row_ids,
                    column_ids=column_ids,
                    validator_name=self.validator_name,
                    sequence=sequence,
                    settings=settings,
                )
                findings.extend(provider_findings)

            if (
                column_set is not None
                and row_set is not None
                and len(column_set.columns) > 0
                and len(row_set.rows) == 0
            ):
                findings.append(
                    build_finding(
                        finding_id=f"GIC-TEMP-EMPTY-{table_id}",
                        category=IntegrityFindingCategory.GENERAL,
                        severity=IntegrityFindingSeverity.WARNING,
                        group_id=group_id,
                        table_id=table_id,
                        message="Cuadro con columnas definidas pero sin filas",
                        validator_name=self.validator_name,
                    ),
                )

            check_sets.append(
                build_check_set(
                    table_id=table_id,
                    group_id=group_id,
                    findings=tuple(findings),
                ),
            )

        set_counts = {
            "structures": len(input_view.structure_catalog.structures),
            "column_sets": len(input_view.column_catalog.column_sets),
            "row_sets": len(input_view.row_catalog.row_sets),
            "provider_sets": len(input_view.provider_catalog.provider_sets),
        }
        unique_counts = set(set_counts.values())
        if len(unique_counts) > 1:
            global_findings.append(
                build_finding(
                    finding_id=f"GIC-GLOBAL-COUNT",
                    category=IntegrityFindingCategory.GENERAL,
                    severity=IntegrityFindingSeverity.WARNING,
                    group_id="",
                    table_id="",
                    message=(
                        "Cantidad inconsistente de conjuntos entre catálogos: "
                        + ", ".join(f"{k}={v}" for k, v in set_counts.items())
                    ),
                    validator_name=self.validator_name,
                    metadata=set_counts,
                ),
            )

        total_findings = sum(len(cs.findings) for cs in check_sets) + len(global_findings)
        return IntegrityValidatorResult(
            validator_type=self.validator_type.value,
            validator_name=self.validator_name,
            check_sets=tuple(check_sets),
            global_findings=tuple(global_findings),
            technical_observations=(
                f"validator_type={self.validator_type.value}",
                f"check_sets_validated={len(check_sets)}",
                f"findings_detected={total_findings}",
                f"tables_evaluated={len(all_table_ids)}",
            ),
        )
