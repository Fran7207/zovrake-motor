"""Regla: estructura documental inconsistente."""

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, metadata_flag, passed_result


class InconsistentStructureRule(ValidationRulePort):
    """Detecta estructuras documentales inconsistentes mediante metadatos."""

    @property
    def rule_name(self) -> str:
        return "inconsistent_structure_rule"

    @property
    def rule_label(self) -> str:
        return "Estructura Inconsistente"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.INCONSISTENT_STRUCTURE

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if metadata_flag(request, "inconsistent_structure"):
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message="Estructura documental inconsistente detectada",
            )
        return passed_result(self.rule_name)
