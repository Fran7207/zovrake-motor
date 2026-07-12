"""Ejecutor de reglas de validación documental."""

from __future__ import annotations

from zovrake_motor.comprehension.validation.enums import DocumentQualityLevel, ValidationStatus
from zovrake_motor.comprehension.validation.models import (
    DocumentValidationRequest,
    DocumentValidationResult,
    ValidationRuleResult,
)
from zovrake_motor.comprehension.validation.registry import ValidationRuleRegistry


class ValidationExecutor:
    """
    Ejecuta el catálogo de reglas y consolida un resultado uniforme.

    No interpreta documentos ni ejecuta OCR en esta etapa.
    """

    def __init__(self, registry: ValidationRuleRegistry) -> None:
        self._registry = registry

    def execute(self, request: DocumentValidationRequest) -> DocumentValidationResult:
        rule_results: list[ValidationRuleResult] = []
        for rule in self._registry.all_rules():
            rule_results.append(rule.validate(request))

        incidents = tuple(
            incident
            for result in rule_results
            for incident in result.incidents
        )
        warnings = tuple(
            warning
            for result in rule_results
            for warning in result.warnings
        )
        observations = tuple(
            observation
            for result in rule_results
            for observation in result.technical_observations
        )

        rules_passed = sum(1 for result in rule_results if result.passed)
        status = self._resolve_status(incidents=incidents, warnings=warnings)
        quality_level = self._resolve_quality_level(status=status, warnings=warnings)

        return DocumentValidationResult(
            process_id=request.process_id,
            document_id=request.document_id,
            status=status,
            incidents=incidents,
            warnings=warnings,
            quality_level=quality_level,
            technical_observations=observations,
            rules_executed=len(rule_results),
            rules_passed=rules_passed,
        )

    def _resolve_status(self, *, incidents, warnings) -> ValidationStatus:
        if incidents:
            return ValidationStatus.FAILED
        if warnings:
            return ValidationStatus.WARNING
        return ValidationStatus.PASSED

    def _resolve_quality_level(self, *, status: ValidationStatus, warnings) -> DocumentQualityLevel:
        if status == ValidationStatus.FAILED:
            return DocumentQualityLevel.LOW
        if warnings:
            return DocumentQualityLevel.ACCEPTABLE
        if status == ValidationStatus.PASSED:
            return DocumentQualityLevel.HIGH
        return DocumentQualityLevel.UNKNOWN
