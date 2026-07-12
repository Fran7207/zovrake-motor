"""Pruebas del Context Integration Engine — Implementación 2.9."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension import ComprehensionRequest
from zovrake_motor.comprehension.context_integration import (
    ContextInputError,
    ContextIntegrationEngine,
    ContextIntegrationRequest,
    DuplicateContextAssociationError,
)
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentContextIntegrationSettings
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_document_knowledge_index import build_internal_model_result


def build_index_result(*, process_id=None, document_id: str = "DOC-001"):
    process_id = process_id or uuid4()
    from zovrake_motor.comprehension.knowledge_index import DocumentKnowledgeIndex

    engine = DocumentKnowledgeIndex()
    engine.initialize()
    model_result = build_internal_model_result(process_id=process_id, document_id=document_id)
    return engine.register(
        DocumentIndexRequest(
            process_id=process_id,
            model_result=model_result,
            validation_reference="dvf://DOC-001",
        ),
    )


class TestContextIntegrationEngine:
    def test_engine_initializes_correctly(self):
        engine = ContextIntegrationEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.store.count() == 0
        assert engine.dki_association.is_prepared is True
        assert engine.classification_integration.is_prepared is True
        assert engine.reasoning_integration.is_prepared is True

    def test_integrates_context_from_detalles_requerimiento(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)
        detalles = "Se requiere cotización de materiales para obra civil con entrega urgente."

        result = engine.integrate(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento=detalles,
                index_result=index_result,
                model_result=model_result,
                requirement_code="REQ-001",
            ),
        )

        assert result.context_id.startswith("ctx://")
        assert result.association.context.description == detalles
        assert result.document_unmodified is True
        assert result.associations_count == 1

    def test_context_model_has_uniform_structure(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)

        result = engine.integrate(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento="Detalles de prueba",
                index_result=index_result,
                model_result=model_result,
            ),
        )

        context = result.association.context
        assert context.immutable is True
        assert context.metadata["source_field"] == "detalles_requerimiento"
        assert context.observations == ()
        assert context.priorities == ()
        assert context.restrictions == ()
        assert context.additional_notes == ()

    def test_traceability_chain_remains_intact(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)

        result = engine.integrate(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento="Contexto trazable",
                index_result=index_result,
                model_result=model_result,
            ),
        )

        trace = result.association.traceability
        model_trace = model_result.model.traceability
        assert trace.document_id == model_trace.document_id
        assert trace.model_id == model_trace.model_id
        assert trace.index_id == index_result.index_id
        assert trace.canonical_reference_id == model_trace.canonical_reference_id
        assert trace.document_unmodified is True
        assert trace.original_preserved is True

    def test_document_information_remains_unmodified(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)
        original_model_dict = model_result.model.to_dict()

        engine.integrate(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento="No debe alterar el modelo",
                index_result=index_result,
                model_result=model_result,
            ),
        )

        assert model_result.model.to_dict() == original_model_dict

    def test_prevents_duplicate_associations(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)
        request = ContextIntegrationRequest(
            process_id=process_id,
            detalles_requerimiento="Contexto duplicado",
            index_result=index_result,
            model_result=model_result,
        )

        engine.integrate(request)

        with pytest.raises(DuplicateContextAssociationError):
            engine.integrate(request)

    def test_rejects_unauthorized_context_source(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)

        with pytest.raises(ContextInputError):
            engine.integrate(
                ContextIntegrationRequest(
                    process_id=process_id,
                    detalles_requerimiento="Contexto",
                    index_result=index_result,
                    model_result=model_result,
                    metadata={"source_field": "otra_fuente"},
                ),
            )

    def test_registers_dki_association_without_modifying_index(self):
        engine = ContextIntegrationEngine()
        engine.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)

        result = engine.integrate(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento="Asociación DKI",
                index_result=index_result,
                model_result=model_result,
            ),
        )

        assert engine.store.get_context_id_by_index(index_result.index_id) == result.context_id


class TestContextIntegrationIntegration:
    def test_pipeline_executes_context_integration_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = service.index_document(
            DocumentIndexRequest(
                process_id=process_id,
                model_result=model_result,
            ),
        )

        result = service.integrate_context(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento="Integración vía pipeline",
                index_result=index_result,
                model_result=model_result,
            ),
        )

        assert result.association.status.value == "integrated"

    def test_context_stage_follows_indexing_in_pipeline(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.INDEXACION) < phases.index(
            ComprehensionPhase.INTEGRACION_CONTEXTO,
        )

    def test_context_manager_component_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        manager = service.component_registry.get("context_manager")
        assert manager is not None
        assert manager.is_ready() is True

    def test_state_and_event_integration_on_context_integration(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        model_result = build_internal_model_result(process_id=process_id)
        index_result = build_index_result(process_id=process_id)

        service.integrate_context(
            ContextIntegrationRequest(
                process_id=process_id,
                detalles_requerimiento="Estados y eventos",
                index_result=index_result,
                model_result=model_result,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_uses_central_configuration(self):
        settings = ComprehensionSettings(
            context_integration=DocumentContextIntegrationSettings(
                classification_integration_prepared=False,
                reasoning_integration_prepared=False,
            ),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        engine = ContextIntegrationEngine(config_provider=provider)
        engine.initialize()

        assert engine.classification_integration.is_prepared is False
        assert engine.reasoning_integration.is_prepared is False

    def test_service_ready_count_includes_context_integration(self):
        service = ComprehensionService()
        service.initialize()

        result = service.prepare(
            ComprehensionRequest(
                process_id=uuid4(),
                codigo_req="REQ-CIE",
            ),
        )

        assert result.components_ready == 9
