"""Pruebas de certificación integral del Módulo de Razonamiento Inteligente — Implementación 7.9."""

from __future__ import annotations

import json
from uuid import uuid4

from zovrake_motor import IntelligentAnalysisService
from zovrake_motor.certification import CoreCertificationChecker, run_full_intelligent_analysis_pipeline
from zovrake_motor.certification.intelligent_analysis_checker import (
    IntelligentAnalysisModuleCertificationChecker,
)
from zovrake_motor.certification.intelligent_analysis_fixtures import (
    build_definitive_catalog_for_certification,
)
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


class TestIntelligentAnalysisModuleCertification:
    def test_intelligent_analysis_certification_passes(self):
        checks = IntelligentAnalysisModuleCertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_full_core_certification_includes_intelligent_analysis_module(self):
        report = CoreCertificationChecker().run()
        areas = {check.area for check in report.checks}
        assert CertificationArea.INTELLIGENT_ANALYSIS_MODULE in areas
        assert CertificationArea.PROMPT_MAESTRO_7 in areas
        assert report.certified_prompt_maestro_7_complete

    def test_full_pipeline_executes_all_functional_stages(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _, _ = build_definitive_catalog_for_certification(
            process_id=process_id,
            document_id="DOC-INTEGRATION",
        )
        result = run_full_intelligent_analysis_pipeline(
            service,
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        )

        assert result.complete
        assert result.stages_executed == 7
        assert result.evidence_analysis_passed
        assert result.consistency_evaluation_passed
        assert result.risk_analysis_passed
        assert result.context_evaluation_passed
        assert result.explanation_generation_passed
        assert result.recommendation_generation_passed
        assert result.reasoning_result_build_passed

    def test_pipeline_phase_order_is_certified(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.CONSUMO_MODELO_COMPARATIVO_DEFINITIVO) < phases.index(
            IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS,
        )
        assert phases.index(IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS) < phases.index(
            IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA,
        )
        assert phases.index(IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA) < phases.index(
            IntelligentAnalysisPhase.ANALISIS_RIESGOS,
        )
        assert phases.index(IntelligentAnalysisPhase.ANALISIS_RIESGOS) < phases.index(
            IntelligentAnalysisPhase.EVALUACION_CONTEXTO,
        )
        assert phases.index(IntelligentAnalysisPhase.EVALUACION_CONTEXTO) < phases.index(
            IntelligentAnalysisPhase.GENERACION_EXPLICACIONES,
        )
        assert phases.index(IntelligentAnalysisPhase.GENERACION_EXPLICACIONES) < phases.index(
            IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES,
        )
        assert phases.index(IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES) < phases.index(
            IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE,
        )
        assert phases.index(IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE) < phases.index(
            IntelligentAnalysisPhase.FINALIZACION,
        )

    def test_traceability_preserved_across_full_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
        result = run_full_intelligent_analysis_pipeline(
            service,
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        )
        assert result.traceability_intact

    def test_source_immutability_preserved_across_full_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
        result = run_full_intelligent_analysis_pipeline(
            service,
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        )
        assert result.definitive_catalog_preserved
        assert result.source_catalogs_preserved

    def test_output_contract_prepared_for_erp(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
        result = run_full_intelligent_analysis_pipeline(
            service,
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        )
        assert result.pm7_output_contract_valid
        assert result.integration_certification_framework_prepared

    def test_coordinator_controls_intelligent_analysis_module(self):
        config = ConfigurationProvider.default()
        coordinator = MotorCoordinator(config_provider=config)
        service = IntelligentAnalysisService(config_provider=config)
        service.initialize()
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()
        assert coordinator.is_module_available("intelligent_analysis")

    def test_states_and_events_during_full_pipeline(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _, _ = build_definitive_catalog_for_certification(process_id=process_id)
        run_full_intelligent_analysis_pipeline(
            service,
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_all_functional_pipeline_components_ready_after_initialization(self):
        service = IntelligentAnalysisService()
        service.initialize()
        snapshot = IntelligentAnalysisPipeline.build_snapshot(service.component_registry)

        functional_components = {
            "evidence_analysis_engine",
            "consistency_evaluation_engine",
            "risk_analysis_engine",
            "context_evaluation_engine",
            "explanation_generation_engine",
            "recommendation_generation_engine",
            "reasoning_result_builder",
        }
        for stage in snapshot:
            if stage.get("component_name") in functional_components:
                assert stage["component_registered"] is True
                assert stage["component_ready"] is True
