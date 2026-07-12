"""Regla: documento ilegible."""

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, metadata_flag, passed_result, warning_result


class IllegibleDocumentRule(ValidationRulePort):
    """Detecta documentos ilegibles mediante metadatos estructurales."""

    @property
    def rule_name(self) -> str:
        return "illegible_document_rule"

    @property
    def rule_label(self) -> str:
        return "Documento Ilegible"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.ILLEGIBLE_DOCUMENT

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if metadata_flag(request, "illegible_document"):
            return warning_result(
                self.rule_name,
                message="Documento potencialmente ilegible",
            )
        return passed_result(self.rule_name)
