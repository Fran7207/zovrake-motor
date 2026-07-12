"""Pruebas del Document Knowledge Index — Implementación 2.8."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension import ComprehensionRequest
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.internal_model import (
    InternalDocumentModelBuilder,
    InternalModelBuildRequest,
)
from zovrake_motor.comprehension.knowledge_index import (
    DocumentKnowledgeIndex,
    DocumentIndexRequest,
    DuplicateIndexEntryError,
    InternalModelInputError,
)
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentKnowledgeIndexSettings
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_document_internal_model import build_canonical_result


def build_internal_model_result(*, process_id=None, document_id: str = "DOC-001", requirement_code: str = "REQ-001"):
    process_id = process_id or uuid4()
    engine = InternalDocumentModelBuilder()
    engine.initialize()
    return engine.build(
        InternalModelBuildRequest(
            process_id=process_id,
            canonical_result=build_canonical_result(process_id=process_id, document_id=document_id),
            requirement_code=requirement_code,
        ),
    )


class TestDocumentKnowledgeIndex:
    def test_engine_initializes_correctly(self):
        engine = DocumentKnowledgeIndex()
        engine.initialize()

        assert engine.is_ready()
        assert engine.store.count() == 0
        assert engine.query_integration.is_prepared is True
        assert engine.reuse_integration.is_prepared is True

    def test_registers_internal_model_with_unique_index_id(self):
        engine = DocumentKnowledgeIndex()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)

        result = engine.register(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
                validation_reference="dvf://DOC-001",
                project_id="PRJ-001",
            ),
        )

        assert result.index_id == f"dki://{model_result.model.model_id}"
        assert result.entries_count == 1
        assert result.duplicate_prevented is True
        assert result.original_preserved is True

    def test_traceability_chain_remains_intact(self):
        engine = DocumentKnowledgeIndex()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)

        result = engine.register(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
                validation_reference="dvf://DOC-001",
            ),
        )

        trace = result.entry.traceability
        model_trace = model_result.model.traceability
        assert trace.document_id == model_trace.document_id
        assert trace.model_id == model_trace.model_id
        assert trace.adapter_name == model_trace.adapter_name
        assert trace.canonical_reference_id == model_trace.canonical_reference_id
        assert trace.extraction_reference_id == model_trace.extraction_reference_id
        assert trace.document_reference == model_trace.document_reference
        assert trace.original_preserved is True
        assert trace.validation_reference == "dvf://DOC-001"

    def test_prevents_duplicate_registrations(self):
        engine = DocumentKnowledgeIndex()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        request = DocumentIndexRequest(process_id=process_id, model_result=model_result)

        engine.register(request)

        with pytest.raises(DuplicateIndexEntryError):
            engine.register(request)

    def test_rejects_invalid_internal_model_input(self):
        engine = DocumentKnowledgeIndex()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)

        with pytest.raises(InternalModelInputError):
            engine.register(
                DocumentIndexRequest(
                    process_id=uuid4(),
                    model_result=model_result,
                ),
            )

    def test_query_keys_prepared_for_future_queries(self):
        engine = DocumentKnowledgeIndex()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)

        result = engine.register(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
                project_id="PRJ-QUERY",
                metadata={"date": "2026-07-10"},
            ),
        )

        keys = result.entry.query_keys
        assert keys["document_id"] == "DOC-001"
        assert keys["project_id"] == "PRJ-QUERY"
        assert keys["requirement_code"] == "REQ-001"
        assert keys["date"] == "2026-07-10"
        assert result.entry.reuse_prepared is True
        assert result.entry.query_integration_prepared is True


class TestKnowledgeIndexIntegration:
    def test_pipeline_executes_index_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)

        result = service.index_document(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
                validation_reference="dvf://DOC-001",
            ),
        )

        assert result.index_id.startswith("dki://")
        assert result.entries_count == 1

    def test_index_stage_follows_modeling_in_pipeline(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.MODELADO) < phases.index(
            ComprehensionPhase.INDEXACION,
        )

    def test_document_index_component_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        index = service.component_registry.get("document_index")
        assert index is not None
        assert index.is_ready() is True

    def test_state_and_event_integration_on_indexing(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)

        service.index_document(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_uses_central_configuration(self):
        settings = ComprehensionSettings(
            knowledge_index=DocumentKnowledgeIndexSettings(
                query_integration_prepared=False,
                reuse_integration_prepared=False,
            ),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        engine = DocumentKnowledgeIndex(config_provider=provider)
        engine.initialize()

        assert engine.query_integration.is_prepared is False
        assert engine.reuse_integration.is_prepared is False

    def test_service_ready_count_includes_knowledge_index(self):
        service = ComprehensionService()
        service.initialize()

        result = service.prepare(
            ComprehensionRequest(
                process_id=uuid4(),
                codigo_req="REQ-DKI",
            ),
        )

        assert result.components_ready == 9
