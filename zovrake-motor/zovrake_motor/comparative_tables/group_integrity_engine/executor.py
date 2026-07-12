"""Ejecutor de validadores del Group Integrity Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.group_integrity_engine.checks import build_integrity_report
from zovrake_motor.comparative_tables.group_integrity_engine.enums import (
    GroupIntegrityValidationStatus,
    IntegrityFindingSeverity,
)
from zovrake_motor.comparative_tables.group_integrity_engine.gateway import (
    IntegrityValidationInputView,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityCheckSet,
    GroupIntegrityFinding,
    GroupIntegrityValidationResult,
)
from zovrake_motor.comparative_tables.group_integrity_engine.registry import (
    IntegrityValidatorRegistry,
)
from zovrake_motor.config.categories.comparative_tables import GroupIntegrityEngineSettings


class GroupIntegrityValidationExecutor:
    """Coordina validadores sin modificar catálogos de entrada."""

    def __init__(self, registry: IntegrityValidatorRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: IntegrityValidationInputView,
        *,
        settings: GroupIntegrityEngineSettings,
    ) -> GroupIntegrityValidationResult:
        check_sets: list[GroupIntegrityCheckSet] = []
        global_findings: list[GroupIntegrityFinding] = []
        observations: list[str] = []
        sequence = 1

        for validator in self._registry.all_validators():
            result = validator.validate(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            check_sets.extend(result.check_sets)
            global_findings.extend(result.global_findings)
            observations.extend(result.technical_observations)
            sequence += sum(len(cs.findings) for cs in result.check_sets) + len(
                result.global_findings,
            )

        all_findings = [
            finding
            for check_set in check_sets
            for finding in check_set.findings
        ] + list(global_findings)

        error_count = sum(
            1 for f in all_findings if f.severity == IntegrityFindingSeverity.ERROR
        )
        warning_count = sum(
            1 for f in all_findings if f.severity == IntegrityFindingSeverity.WARNING
        )

        if error_count >= settings.max_errors_before_invalid:
            status = GroupIntegrityValidationStatus.INVALID
        elif warning_count > 0:
            status = GroupIntegrityValidationStatus.PARTIAL
        elif check_sets:
            status = GroupIntegrityValidationStatus.VALID
        else:
            status = GroupIntegrityValidationStatus.SKIPPED

        report = build_integrity_report(
            input_view=input_view,
            check_sets=tuple(check_sets),
            global_findings=tuple(global_findings),
            traceability_metadata_engine_prepared=settings.traceability_metadata_engine_prepared,
        )

        observations.extend(
            (
                "structure_catalog_preserved=True",
                "column_catalog_preserved=True",
                "row_catalog_preserved=True",
                "provider_catalog_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "findings_count=" + str(len(all_findings)),
                "error_count=" + str(error_count),
                "warning_count=" + str(warning_count),
            ),
        )

        return GroupIntegrityValidationResult(
            process_id=input_view.provider_catalog.process_id,
            document_id=input_view.provider_catalog.document_id,
            model_id=input_view.provider_catalog.model_id,
            report=report,
            status=status,
            findings_count=len(all_findings),
            error_count=error_count,
            warning_count=warning_count,
            structure_catalog_preserved=True,
            column_catalog_preserved=True,
            row_catalog_preserved=True,
            provider_catalog_preserved=True,
            domain_model_preserved=input_view.provider_catalog.domain_model_preserved,
            validators_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
