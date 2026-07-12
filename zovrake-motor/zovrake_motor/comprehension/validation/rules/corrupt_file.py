"""Regla: archivo corrupto."""

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, metadata_flag, passed_result


class CorruptFileRule(ValidationRulePort):
    """Detecta archivos corruptos mediante metadatos estructurales."""

    @property
    def rule_name(self) -> str:
        return "corrupt_file_rule"

    @property
    def rule_label(self) -> str:
        return "Archivo Corrupto"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.CORRUPT_FILE

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if metadata_flag(request, "corrupt_file"):
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message="Archivo corrupto detectado",
            )
        return passed_result(self.rule_name)
