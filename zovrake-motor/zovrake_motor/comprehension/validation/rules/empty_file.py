"""Regla: archivo vacío."""

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, metadata_flag, passed_result


class EmptyFileRule(ValidationRulePort):
    """Detecta archivos vacíos mediante metadatos estructurales."""

    @property
    def rule_name(self) -> str:
        return "empty_file_rule"

    @property
    def rule_label(self) -> str:
        return "Archivo Vacío"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.EMPTY_FILE

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if request.file_size_bytes == 0 or metadata_flag(request, "empty_file"):
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message="Archivo vacío detectado",
            )
        return passed_result(self.rule_name)
