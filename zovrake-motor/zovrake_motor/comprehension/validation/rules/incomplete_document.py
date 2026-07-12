"""Regla: documento incompleto."""

from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, ValidationRuleResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.rules.base import failed_result, metadata_flag, passed_result


class IncompleteDocumentRule(ValidationRulePort):
    """Detecta documentos incompletos mediante metadatos estructurales."""

    @property
    def rule_name(self) -> str:
        return "incomplete_document_rule"

    @property
    def rule_label(self) -> str:
        return "Documento Incompleto"

    @property
    def incident_type(self) -> ValidationIncidentType:
        return ValidationIncidentType.INCOMPLETE_DOCUMENT

    def validate(self, request: DocumentValidationRequest) -> ValidationRuleResult:
        if metadata_flag(request, "incomplete_document"):
            return failed_result(
                self.rule_name,
                incident_type=self.incident_type,
                message="Documento incompleto detectado",
            )
        return passed_result(self.rule_name)
