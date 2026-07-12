"""Pruebas de certificación integral del Módulo de Clasificación Inteligente — Implementación 3.11."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.certification import CoreCertificationChecker, run_full_classification_pipeline
from zovrake_motor.certification.classification_checker import ClassificationModuleCertificationChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


class TestClassificationModuleCertification:
    def test_classification_certification_passes(self):
        checks = ClassificationModuleCertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_full_core_certification_includes_classification_module(self):
        report = CoreCertificationChecker().run()
        areas = {check.area for check in report.checks}
        assert CertificationArea.CLASSIFICATION_MODULE in areas
        assert CertificationArea.PROMPT_MAESTRO_5 in areas
        assert report.certified_prompt_maestro_5_complete

    def test_full_pipeline_executes_all_functional_stages(self):
        service = ClassificationService()
        service.initialize()
        result = run_full_classification_pipeline(
            service,
            process_id=uuid4(),
            document_id="DOC-INTEGRATION",
        )

        assert result.complete
        assert result.stages_executed == 9
        assert result.concept_analysis_passed
        assert result.material_classification_passed
        assert result.service_classification_passed
        assert result.concept_normalization_passed
        assert result.equivalence_detection_passed
        assert result.comparable_group_build_passed
        assert result.context_association_passed
        assert result.comparative_domain_model_passed
        assert result.quality_validation_passed

    def test_pipeline_phase_order_is_certified(self):
        phases = ClassificationPipeline.ordered_phases()
        assert phases.index(ClassificationPhase.ANALISIS_CONCEPTOS) < phases.index(
            ClassificationPhase.CLASIFICACION_MATERIALES,
        )
        assert phases.index(ClassificationPhase.CLASIFICACION_MATERIALES) < phases.index(
            ClassificationPhase.CLASIFICACION_SERVICIOS,
        )
        assert phases.index(ClassificationPhase.NORMALIZACION_CONCEPTOS) < phases.index(
            ClassificationPhase.DETECCION_EQUIVALENCIAS,
        )
        assert phases.index(ClassificationPhase.CONSTRUCCION_GRUPOS) < phases.index(
            ClassificationPhase.ASOCIACION_CONTEXTO,
        )
        assert phases.index(ClassificationPhase.MODELO_DOMINIO) < phases.index(
            ClassificationPhase.VALIDACION_CALIDAD,
        )
        assert phases.index(ClassificationPhase.VALIDACION_CALIDAD) < phases.index(
            ClassificationPhase.FINALIZACION,
        )

    def test_traceability_preserved_across_full_pipeline(self):
        service = ClassificationService()
        service.initialize()
        result = run_full_classification_pipeline(service, process_id=uuid4())
        assert result.traceability_intact

    def test_source_immutability_preserved_across_full_pipeline(self):
        service = ClassificationService()
        service.initialize()
        result = run_full_classification_pipeline(service, process_id=uuid4())
        assert result.source_data_immutable

    def test_materials_and_services_remain_separated(self):
        service = ClassificationService()
        service.initialize()
        result = run_full_classification_pipeline(service, process_id=uuid4())
        assert result.materials_services_separated

    def test_coordinator_controls_classification_module(self):
        config = ConfigurationProvider.default()
        coordinator = MotorCoordinator(config_provider=config)
        service = ClassificationService(config_provider=config)
        service.initialize()
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()
        assert coordinator.is_module_available("classification")

    def test_states_and_events_during_full_pipeline(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ClassificationService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        run_full_classification_pipeline(service, process_id=process_id)

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_all_functional_pipeline_components_ready_after_initialization(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)

        functional_components = {
            "concept_analysis_engine",
            "material_classification_engine",
            "service_classification_engine",
            "concept_normalization_engine",
            "equivalence_detection_engine",
            "comparable_group_builder",
            "context_association_engine",
            "comparative_domain_model_builder",
            "classification_quality_framework",
        }
        for stage in snapshot:
            if stage.get("component_name") in functional_components:
                assert stage["component_registered"] is True
                assert stage["component_ready"] is True

    def test_central_configuration_covers_all_engines(self):
        classification = ConfigurationProvider.default().classification()
        for attr in (
            "concept_analysis",
            "material_classification",
            "service_classification",
            "concept_normalization",
            "equivalence_detection",
            "comparable_group_builder",
            "context_association",
            "comparative_domain_model_builder",
            "classification_quality_framework",
        ):
            assert hasattr(classification, attr)

    def test_comparative_domain_model_prepared_for_pm6(self):
        service = ClassificationService()
        service.initialize()
        result = run_full_classification_pipeline(service, process_id=uuid4())
        assert result.comparative_domain_model_passed
        assert result.certification_prepared
