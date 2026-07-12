"""Pruebas de certificación integral del Módulo de Comprensión Documental — Implementación 2.10."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from zovrake_motor import ComprehensionService
from zovrake_motor.certification.comprehension_checker import ComprehensionModuleCertificationChecker
from zovrake_motor.certification import CoreCertificationChecker, run_full_comprehension_pipeline
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


class TestComprehensionModuleCertification:
    def test_comprehension_certification_passes(self):
        checks = ComprehensionModuleCertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_full_core_certification_includes_comprehension_module(self):
        report = CoreCertificationChecker().run()
        areas = {check.area for check in report.checks}
        assert CertificationArea.COMPREHENSION_MODULE in areas
        assert report.certified_prompt_maestro_4_complete

    def test_full_pipeline_executes_all_functional_stages(self):
        service = ComprehensionService()
        service.initialize()
        result = run_full_comprehension_pipeline(
            service,
            process_id=uuid4(),
            document_id="DOC-INTEGRATION",
        )

        assert result.complete
        assert result.stages_executed == 7
        assert result.validation_passed
        assert result.recognition_passed
        assert result.extraction_passed
        assert result.canonical_passed
        assert result.internal_model_passed
        assert result.indexing_passed
        assert result.context_integration_passed

    def test_pipeline_phase_order_is_certified(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.VALIDACION) < phases.index(ComprehensionPhase.IDENTIFICACION)
        assert phases.index(ComprehensionPhase.EXTRACCION) < phases.index(ComprehensionPhase.NORMALIZACION)
        assert phases.index(ComprehensionPhase.MODELADO) < phases.index(ComprehensionPhase.INDEXACION)
        assert phases.index(ComprehensionPhase.INDEXACION) < phases.index(ComprehensionPhase.INTEGRACION_CONTEXTO)
        assert phases.index(ComprehensionPhase.INTEGRACION_CONTEXTO) < phases.index(ComprehensionPhase.FINALIZACION)

    def test_traceability_preserved_across_full_pipeline(self):
        service = ComprehensionService()
        service.initialize()
        result = run_full_comprehension_pipeline(service, process_id=uuid4())
        assert result.traceability_intact

    def test_document_immutability_preserved_across_full_pipeline(self):
        service = ComprehensionService()
        service.initialize()
        result = run_full_comprehension_pipeline(service, process_id=uuid4())
        assert result.document_unmodified

    def test_context_correctly_associated_after_pipeline(self):
        service = ComprehensionService()
        service.initialize()
        result = run_full_comprehension_pipeline(
            service,
            process_id=uuid4(),
            detalles_requerimiento="Contexto de certificación integral",
        )
        assert result.context_associated
        assert result.context_integration_passed

    def test_coordinator_controls_comprehension_module(self):
        config = ConfigurationProvider.default()
        coordinator = MotorCoordinator(config_provider=config)
        service = ComprehensionService(config_provider=config)
        service.initialize()
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()
        assert coordinator.is_module_available("comprehension")

    def test_states_and_events_during_full_pipeline(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        run_full_comprehension_pipeline(service, process_id=process_id)

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_all_pipeline_components_ready_after_initialization(self):
        service = ComprehensionService()
        service.initialize()
        snapshot = DocumentComprehensionPipeline.build_snapshot(service.component_registry)

        for stage in snapshot:
            if stage.get("component_name"):
                assert stage["component_registered"] is True
                assert stage["component_ready"] is True

    def test_central_configuration_covers_all_engines(self):
        comprehension = ConfigurationProvider.default().comprehension()
        for attr in (
            "adapters",
            "validation",
            "recognition",
            "extraction",
            "canonical",
            "internal_model",
            "knowledge_index",
            "context_integration",
        ):
            assert hasattr(comprehension, attr)
