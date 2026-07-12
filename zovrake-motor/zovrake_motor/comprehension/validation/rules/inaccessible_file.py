"""Regla: archivo inaccesible."""

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, metadata_flag, passed_result


class InaccessibleFileRule(ValidationRulePort):
    """Detecta archivos inaccesibles mediante metadatos estructurales."""

    @property
    def rule_name(self) -> str:
        return "inaccessible_file_rule"

    @property
    def rule_label(self) -> str:
        return "Archivo Inaccesible"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.INACCESSIBLE_FILE

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if request.accessible is False or metadata_flag(request, "inaccessible_file"):
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message="Archivo inaccesible detectado",
            )
        return passed_result(self.rule_name)
