"""Pruebas del Document Recognition Engine — Implementación 2.4."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension.adapters import DocumentAdapterFramework, DocumentFormatType
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.comprehension.recognition import (
    DocumentRecognitionEngine,
    DocumentRecognitionRequest,
    FormatCatalog,
    RecognitionStrategyPort,
    RecognitionStrategyType,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentRecognitionSettings
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


class TestDocumentRecognitionEngine:
    def test_engine_initializes_with_default_strategies(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 3

    def test_all_strategies_implement_common_contract(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        for strategy in engine.registry.all_strategies():
            assert isinstance(strategy, RecognitionStrategyPort)
            assert strategy.strategy_name
            assert strategy.strategy_label
            assert strategy.strategy_type

    def test_recognizes_pdf_by_extension(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        result = engine.recognize(
            DocumentRecognitionRequest(
                process_id=uuid4(),
                document_id="DOC-PDF",
                file_name="cotizacion.pdf",
            ),
        )

        assert result.recognized is True
        assert result.identified_format == DocumentFormatType.PDF
        assert result.suggested_adapter == "pdf_adapter"
        assert result.strategy_used == "extension_strategy"
        assert result.confidence >= 0.5

    def test_recognizes_word_by_metadata(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        result = engine.recognize(
            DocumentRecognitionRequest(
                process_id=uuid4(),
                document_id="DOC-WORD",
                format_type="docx",
            ),
        )

        assert result.recognized is True
        assert result.identified_format == DocumentFormatType.WORD
        assert result.strategy_used == "metadata_strategy"

    def test_recognizes_image_by_mime_type(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        result = engine.recognize(
            DocumentRecognitionRequest(
                process_id=uuid4(),
                document_id="DOC-IMG",
                mime_type="image/png",
            ),
        )

        assert result.recognized is True
        assert result.identified_format == DocumentFormatType.IMAGE
        assert result.strategy_used == "mime_type_strategy"

    def test_result_has_uniform_structure(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        result = engine.recognize(
            DocumentRecognitionRequest(
                process_id=uuid4(),
                document_id="DOC-STRUCT",
                file_name="archivo.xlsx",
            ),
        )

        payload = result.to_dict()
        assert payload["recognized"] is True
        assert "identified_format" in payload
        assert "confidence" in payload
        assert "confidence_level" in payload
        assert "strategy_used" in payload
        assert "suggested_adapter" in payload
        assert "technical_observations" in payload

    def test_prepares_adapter_selection_without_execution(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()
        adapter_framework = DocumentAdapterFramework()
        adapter_framework.initialize()

        base = engine.recognize(
            DocumentRecognitionRequest(
                process_id=uuid4(),
                document_id="DOC-ADAPTER",
                file_name="informe.pdf",
            ),
        )
        result = engine.prepare_adapter_selection(base, adapter_framework=adapter_framework)

        assert result.adapter_selection is not None
        assert result.adapter_selection.suggested_adapter == "pdf_adapter"
        message = result.adapter_selection.resolution_message.lower()
        assert "sin" in message or "deshabilitado" in message or "adaptador" in message

    def test_format_catalog_maps_all_initial_formats(self):
        assert FormatCatalog.suggested_adapter(DocumentFormatType.PDF) == "pdf_adapter"
        assert FormatCatalog.suggested_adapter(DocumentFormatType.WORD) == "word_adapter"
        assert FormatCatalog.suggested_adapter(DocumentFormatType.EXCEL) == "excel_adapter"
        assert FormatCatalog.suggested_adapter(DocumentFormatType.IMAGE) == "image_adapter"

    def test_engine_extend_registers_new_strategy(self):
        engine = DocumentRecognitionEngine()
        engine.initialize()

        class CustomStrategy(RecognitionStrategyPort):
            @property
            def strategy_type(self) -> RecognitionStrategyType:
                return RecognitionStrategyType.METADATA

            @property
            def strategy_name(self) -> str:
                return "custom_strategy"

            @property
            def strategy_label(self) -> str:
                return "Custom Strategy"

            def recognize(self, request: DocumentRecognitionRequest):
                from zovrake_motor.comprehension.recognition.strategies.base import unrecognized_result

                return unrecognized_result(
                    strategy_type=self.strategy_type,
                    strategy_name=self.strategy_name,
                )

        engine.extend(CustomStrategy())
        assert engine.registry.count() == 4


class TestDocumentRecognitionIntegration:
    def test_pipeline_executes_recognition_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()

        result = service.recognize_document(
            DocumentRecognitionRequest(
                process_id=process_id,
                document_id="DOC-PIPE",
                file_name="documento.pdf",
            ),
        )

        assert result.recognized is True
        assert result.identified_format == DocumentFormatType.PDF

    def test_recognition_stage_follows_validation_in_pipeline(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.VALIDACION) < phases.index(
            ComprehensionPhase.IDENTIFICACION,
        )
        assert phases.index(ComprehensionPhase.ADAPTACION) < phases.index(
            ComprehensionPhase.IDENTIFICACION,
        )

    def test_format_identifier_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        identifier = service.component_registry.get("format_identifier")
        assert identifier is not None
        assert identifier.is_ready() is True

    def test_state_and_event_integration_on_recognition(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        service.recognize_document(
            DocumentRecognitionRequest(
                process_id=process_id,
                document_id="DOC-TRACE",
                file_name="evidencia.docx",
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PREPARANDO_PROCESAMIENTO
        assert event_manager.count() >= 2

    def test_unrecognized_document_records_warning_state(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        result = service.recognize_document(
            DocumentRecognitionRequest(
                process_id=process_id,
                document_id="DOC-UNKNOWN",
                file_name="archivo.desconocido",
            ),
        )

        assert result.recognized is False
        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.INFORMACION_RECIBIDA

    def test_uses_central_configuration(self):
        settings = ComprehensionSettings(
            recognition=DocumentRecognitionSettings(
                magic_number_strategy_enabled=True,
            ),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        engine = DocumentRecognitionEngine(config_provider=provider)
        engine.initialize()

        assert engine.registry.count() == 4
