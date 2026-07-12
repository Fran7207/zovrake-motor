"""Pruebas del Content Extraction Engine — Implementación 2.5."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension import ComprehensionRequest
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.extraction import (
    AdapterAccessError,
    AdapterDocumentContext,
    ContentExtractionEngine,
    ContentExtractionRequest,
    ContentExtractorPort,
    ExtractorType,
    OriginalDocumentModifiedError,
    TextExtractor,
)
from zovrake_motor.comprehension.extraction.models import ExtractorResult
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentExtractionSettings
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


def build_adapter_context(
    *,
    process_id=None,
    document_id: str = "DOC-001",
    adapter_name: str = "pdf_adapter",
    metadata: dict | None = None,
) -> AdapterDocumentContext:
    return AdapterDocumentContext(
        process_id=process_id or uuid4(),
        document_id=document_id,
        adapter_name=adapter_name,
        format_type="pdf",
        document_reference="adapter://pdf/DOC-001",
        original_preserved=True,
        metadata=metadata or {},
    )


class TestContentExtractionEngine:
    def test_engine_initializes_with_default_extractors(self):
        engine = ContentExtractionEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 8

    def test_all_extractors_implement_common_contract(self):
        engine = ContentExtractionEngine()
        engine.initialize()

        for extractor in engine.registry.all_extractors():
            assert isinstance(extractor, ContentExtractorPort)
            assert extractor.extractor_name
            assert extractor.extractor_label
            assert extractor.extractor_type

    def test_extracts_text_from_adapter_metadata(self):
        engine = ContentExtractionEngine()
        engine.initialize()
        process_id = uuid4()

        result = engine.extract(
            ContentExtractionRequest(
                process_id=process_id,
                document_id="DOC-TEXT",
                adapter_context=build_adapter_context(
                    process_id=process_id,
                    document_id="DOC-TEXT",
                    metadata={"text_content": "Contenido de prueba"},
                ),
            ),
        )

        assert "Contenido de prueba" in result.extracted_text
        assert result.original_preserved is True
        assert result.adapter_name == "pdf_adapter"
        assert result.extractors_executed == 8

    def test_result_has_uniform_structure(self):
        engine = ContentExtractionEngine()
        engine.initialize()
        process_id = uuid4()

        result = engine.extract(
            ContentExtractionRequest(
                process_id=process_id,
                document_id="DOC-STRUCT",
                adapter_context=build_adapter_context(process_id=process_id, document_id="DOC-STRUCT"),
            ),
        )

        payload = result.to_dict()
        assert "extracted_text" in payload
        assert "tables" in payload
        assert "metadata" in payload
        assert "structural_elements" in payload
        assert "incidents" in payload
        assert payload["original_preserved"] is True
        assert payload["ocr_integration_prepared"] is True
        assert payload["extractors_executed"] == 8
        assert payload["adapter_name"] == "pdf_adapter"

    def test_rejects_direct_document_access_without_adapter(self):
        engine = ContentExtractionEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(AdapterAccessError):
            engine.extract(
                ContentExtractionRequest(
                    process_id=process_id,
                    document_id="DOC-NO-ADAPTER",
                    adapter_context=AdapterDocumentContext(
                        process_id=process_id,
                        document_id="DOC-NO-ADAPTER",
                        adapter_name="",
                        format_type="pdf",
                        document_reference="",
                    ),
                ),
            )

    def test_rejects_modified_original_document(self):
        engine = ContentExtractionEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(OriginalDocumentModifiedError):
            engine.extract(
                ContentExtractionRequest(
                    process_id=process_id,
                    document_id="DOC-MODIFIED",
                    adapter_context=AdapterDocumentContext(
                        process_id=process_id,
                        document_id="DOC-MODIFIED",
                        adapter_name="pdf_adapter",
                        format_type="pdf",
                        document_reference="adapter://pdf/DOC-MODIFIED",
                        original_preserved=False,
                    ),
                ),
            )

    def test_ocr_integration_prepared_without_execution(self):
        engine = ContentExtractionEngine()
        engine.initialize()

        ocr = engine.ocr_integration
        assert ocr.is_prepared is True
        assert ocr.can_execute() is False
        preparation = ocr.prepare_for_future_execution()
        assert preparation["executed"] is False

    def test_engine_extend_registers_new_extractor(self):
        engine = ContentExtractionEngine()
        engine.initialize()

        class CustomExtractor(ContentExtractorPort):
            @property
            def extractor_name(self) -> str:
                return "custom_extractor"

            @property
            def extractor_label(self) -> str:
                return "Custom Extractor"

            @property
            def extractor_type(self) -> ExtractorType:
                return ExtractorType.METADATA

            def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
                return ExtractorResult(
                    extractor_name=self.extractor_name,
                    extractor_type=self.extractor_type.value,
                    metadata={"custom": True},
                )

        engine.extend(CustomExtractor())
        assert engine.registry.count() == 9


class TestContentExtractionIntegration:
    def test_pipeline_executes_extraction_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()

        result = service.extract_content(
            ContentExtractionRequest(
                process_id=process_id,
                document_id="DOC-PIPE",
                adapter_context=build_adapter_context(
                    process_id=process_id,
                    document_id="DOC-PIPE",
                    metadata={"text_content": "Pipeline extraction"},
                ),
            ),
        )

        assert result.original_preserved is True
        assert result.extractors_executed == 8
        assert "Pipeline extraction" in result.extracted_text

    def test_extraction_stage_follows_recognition_in_pipeline(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.IDENTIFICACION) < phases.index(
            ComprehensionPhase.EXTRACCION,
        )
        assert phases.index(ComprehensionPhase.ADAPTACION) < phases.index(
            ComprehensionPhase.EXTRACCION,
        )

    def test_extractors_component_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        extractors = service.component_registry.get("extractors")
        assert extractors is not None
        assert extractors.is_ready() is True

    def test_state_and_event_integration_on_extraction(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        service.extract_content(
            ContentExtractionRequest(
                process_id=process_id,
                document_id="DOC-TRACE",
                adapter_context=build_adapter_context(
                    process_id=process_id,
                    document_id="DOC-TRACE",
                ),
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_uses_central_configuration(self):
        settings = ComprehensionSettings(
            extraction=DocumentExtractionSettings(
                headers_extractor_enabled=False,
                footers_extractor_enabled=False,
            ),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        engine = ContentExtractionEngine(config_provider=provider)
        engine.initialize()

        assert engine.registry.count() == 6

    def test_service_ready_count_includes_extraction(self):
        service = ComprehensionService()
        service.initialize()

        result = service.prepare(
            ComprehensionRequest(
                process_id=uuid4(),
                codigo_req="REQ-CEE",
            ),
        )

        assert result.components_ready == 9
