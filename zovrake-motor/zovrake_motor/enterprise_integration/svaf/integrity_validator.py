"""Validador de integridad de solicitudes — sin mecanismos criptográficos."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.svaf.enums import IntegrityIssueType
from zovrake_motor.enterprise_integration.svaf.models import ValidationIssue


class RequestIntegrityValidator:
    """
    Verifica que una solicitud no llegue incompleta, alterada o con estructuras inválidas.

    No corrige mensajes automáticamente.
    """

    _OPTIONAL_NULLABLE_KEYS = frozenset({
        "controlled_error",
        "analysis_result",
        "comparative_tables",
        "traceability",
    })

    def __init__(self) -> None:
        self._seen_process_operations: set[tuple[str, str]] = set()

    def check_inbound(
        self,
        *,
        process_id: UUID,
        operation: str,
        payload: dict[str, Any],
    ) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        issues.extend(self._check_completeness(payload))
        issues.extend(self._check_duplicate(process_id, operation))
        issues.extend(self._check_payload_structure(payload))
        return tuple(issues)

    def check_outbound(
        self,
        *,
        process_id: UUID,
        operation: str,
        payload: dict[str, Any],
        inbound_approved: bool,
    ) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        issues.extend(self._check_completeness(payload))
        issues.extend(self._check_payload_structure(payload))
        if not inbound_approved:
            issues.append(
                ValidationIssue(
                    field="pipeline",
                    message="Respuesta inconsistente — solicitud no validada previamente",
                    issue_type=IntegrityIssueType.INCONSISTENT_RESPONSE,
                ),
            )
        return tuple(issues)

    def mark_processed(self, process_id: UUID, operation: str) -> None:
        self._seen_process_operations.add((str(process_id), operation))

    def _check_duplicate(self, process_id: UUID, operation: str) -> list[ValidationIssue]:
        key = (str(process_id), operation)
        if key in self._seen_process_operations:
            return [
                ValidationIssue(
                    field="process_id",
                    message="Mensaje duplicado detectado para la misma operación",
                    issue_type=IntegrityIssueType.DUPLICATE_MESSAGE,
                ),
            ]
        return []

    @staticmethod
    def _check_completeness(payload: dict[str, Any]) -> list[ValidationIssue]:
        if not payload:
            return [
                ValidationIssue(
                    field="payload",
                    message="Mensaje incompleto — payload vacío",
                    issue_type=IntegrityIssueType.INCOMPLETE_MESSAGE,
                ),
            ]
        return []

    def _check_payload_structure(self, payload: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for key, value in payload.items():
            if value is None and key in self._OPTIONAL_NULLABLE_KEYS:
                continue
            if value is None:
                issues.append(
                    ValidationIssue(
                        field=key,
                        message=f"Campo {key} no puede ser nulo",
                        issue_type=IntegrityIssueType.INVALID_STRUCTURE,
                    ),
                )
        return issues

    def snapshot(self) -> dict[str, Any]:
        return {"tracked_operations": len(self._seen_process_operations)}
