"""Pruebas del Document Validation Framework — Implementación 2.3."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.comprehension.validation import (
    DocumentValidationFramework,
    DocumentValidationRequest,
    ValidationRulePort,
    ValidationStatus,
)
from zovrake_motor.comprehension.validation.enums import ValidationIncidentType
from zovrake_motor.comprehension.validation.rules import (
    CorruptFileRule,
    EmptyFileRule,
    IllegibleDocumentRule,
    InaccessibleFileRule,
    IncompleteDocumentRule,
    InconsistentStructureRule,
    InvalidSizeRule,
    UnsupportedFormatRule,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentValidationSettings
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


class TestDocumentValidationFramework:
    def test_framework_initializes_with_eight_rules(self):
        framework = DocumentValidationFramework()
        framework.initialize()

        assert framework.is_ready()
        assert framework.registry.count() == 8

    def test_all_rules_implement_common_contract(self):
        framework = DocumentValidationFramework()
        framework.initialize()

        for rule in framework.registry.all_rules():
            assert isinstance(rule, ValidationRulePort)
            assert rule.rule_name
            assert rule.rule_label
            assert rule.incident_type

    def test_registered_rules_cover_catalog(self):
        framework = DocumentValidationFramework()
        framework.initialize()

        registered = {rule.rule_name for rule in framework.registry.all_rules()}
        assert registered == {
            "empty_file_rule",
            "corrupt_file_rule",
            "unsupported_format_rule",
            "inaccessible_file_rule",
            "incomplete_document_rule",
            "illegible_document_rule",
            "invalid_size_rule",
            "inconsistent_structure_rule",
        }

    def test_validation_result_has_uniform_structure(self):
        framework = DocumentValidationFramework()
        framework.initialize()
        process_id = uuid4()

        result = framework.validate(
            DocumentValidationRequest(
                process_id=process_id,
                document_id="DOC-001",
                format_type="pdf",
                file_size_bytes=1024,
            ),
        )

        payload = result.to_dict()
        assert payload["status"] == ValidationStatus.PASSED.value
        assert payload["rules_executed"] == 8
        assert payload["rules_passed"] == 8
        assert "incidents" in payload
        assert "warnings" in payload
        assert "quality_level" in payload
        assert "technical_observations" in payload

    def test_detects_empty_file_via_metadata(self):
        framework = DocumentValidationFramework()
        framework.initialize()
        process_id = uuid4()

        result = framework.validate(
            DocumentValidationRequest(
                process_id=process_id,
                document_id="DOC-EMPTY",
                file_size_bytes=0,
            ),
        )

        assert result.status == ValidationStatus.FAILED
        assert any(
            incident.incident_type == ValidationIncidentType.EMPTY_FILE
            for incident in result.incidents
        )

    def test_detects_unsupported_format(self):
        settings = ComprehensionSettings(
            validation=DocumentValidationSettings(supported_formats=("pdf",)),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        framework = DocumentValidationFramework(config_provider=provider)
        framework.initialize()

        result = framework.validate(
            DocumentValidationRequest(
                process_id=uuid4(),
                document_id="DOC-FMT",
                format_type="docx",
            ),
        )

        assert result.status == ValidationStatus.FAILED
        assert any(
            incident.incident_type == ValidationIncidentType.UNSUPPORTED_FORMAT
            for incident in result.incidents
        )

    def test_framework_extend_registers_new_rule(self):
        framework = DocumentValidationFramework()
        framework.initialize()

        class CustomRule(ValidationRulePort):
            @property
            def rule_name(self) -> str:
                return "custom_rule"

            @property
            def rule_label(self) -> str:
                return "Custom Rule"

            @property
            def incident_type(self) -> ValidationIncidentType:
                return ValidationIncidentType.INCONSISTENT_STRUCTURE

            def validate(self, request: DocumentValidationRequest):
                from zovrake_motor.comprehension.validation.rules.base import passed_result

                return passed_result(self.rule_name)

        framework.extend(CustomRule())
        assert framework.registry.count() == 9


class TestDocumentValidationIntegration:
    def test_pipeline_executes_validation_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()

        result = service.validate_document(
            DocumentValidationRequest(
                process_id=process_id,
                document_id="DOC-PIPE",
                format_type="pdf",
                file_size_bytes=2048,
            ),
        )

        assert result.status == ValidationStatus.PASSED
        assert result.rules_executed == 8

    def test_validation_stage_is_before_adaptation(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.VALIDACION) < phases.index(
            ComprehensionPhase.ADAPTACION,
        )

    def test_validator_component_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        validator = service.component_registry.get("document_validator")
        assert validator is not None
        assert validator.is_ready() is True

    def test_state_and_event_integration(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        service.validate_document(
            DocumentValidationRequest(
                process_id=process_id,
                document_id="DOC-TRACE",
                format_type="pdf",
                file_size_bytes=512,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.INFORMACION_RECIBIDA
        assert event_manager.count() >= 2

    def test_failed_validation_sets_error_state(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        result = service.validate_document(
            DocumentValidationRequest(
                process_id=process_id,
                document_id="DOC-FAIL",
                metadata={"corrupt_file": True},
            ),
        )

        assert result.status == ValidationStatus.FAILED
        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.ERROR_VALIDACION

    def test_individual_rules_are_independent(self):
        rules = (
            EmptyFileRule(),
            CorruptFileRule(),
            UnsupportedFormatRule(),
            InaccessibleFileRule(),
            IncompleteDocumentRule(),
            IllegibleDocumentRule(),
            InvalidSizeRule(),
            InconsistentStructureRule(),
        )
        assert len({rule.rule_name for rule in rules}) == 8
        assert len({rule.incident_type for rule in rules}) == 8
