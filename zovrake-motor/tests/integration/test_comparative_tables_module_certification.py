"""Pruebas de certificación integral del Módulo de Generación de Cuadros Comparativos — Implementación 4.11."""

from __future__ import annotations

import json
from uuid import uuid4

from zovrake_motor import ComparativeTablesService
from zovrake_motor.certification import CoreCertificationChecker, run_full_comparative_tables_pipeline
from zovrake_motor.certification.comparative_tables_checker import (
    ComparativeTablesModuleCertificationChecker,
)
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


class TestComparativeTablesModuleCertification:
    def test_comparative_tables_certification_passes(self):
        checks = ComparativeTablesModuleCertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_full_core_certification_includes_comparative_tables_module(self):
        report = CoreCertificationChecker().run()
        areas = {check.area for check in report.checks}
        assert CertificationArea.COMPARATIVE_TABLES_MODULE in areas
        assert CertificationArea.PROMPT_MAESTRO_6 in areas
        assert report.certified_prompt_maestro_6_complete

    def test_full_pipeline_executes_all_functional_stages(self):
        service = ComparativeTablesService()
        service.initialize()
        result = run_full_comparative_tables_pipeline(
            service,
            process_id=uuid4(),
            document_id="DOC-INTEGRATION",
        )

        assert result.complete
        assert result.stages_executed == 9
        assert result.structure_build_passed
        assert result.column_build_passed
        assert result.row_build_passed
        assert result.provider_organization_passed
        assert result.group_integrity_passed
        assert result.traceability_enrichment_passed
        assert result.comparative_model_build_passed
        assert result.validation_passed
        assert result.quality_audit_passed

    def test_pipeline_phase_order_is_certified(self):
        phases = ComparativeTablesPipeline.ordered_phases()
        assert phases.index(ComparativeTablesPhase.CONSUMO_MODELO_DOMINIO) < phases.index(
            ComparativeTablesPhase.ESTRUCTURA_COMPARATIVA,
        )
        assert phases.index(ComparativeTablesPhase.ESTRUCTURA_COMPARATIVA) < phases.index(
            ComparativeTablesPhase.CONSTRUCCION_COLUMNAS,
        )
        assert phases.index(ComparativeTablesPhase.CONSTRUCCION_COLUMNAS) < phases.index(
            ComparativeTablesPhase.CONSTRUCCION_FILAS,
        )
        assert phases.index(ComparativeTablesPhase.ORGANIZACION_PROVEEDORES) < phases.index(
            ComparativeTablesPhase.INTEGRIDAD_GRUPOS,
        )
        assert phases.index(ComparativeTablesPhase.TRAZABILIDAD_METADATOS) < phases.index(
            ComparativeTablesPhase.MODELO_COMPARATIVO,
        )
        assert phases.index(ComparativeTablesPhase.MODELO_COMPARATIVO) < phases.index(
            ComparativeTablesPhase.VALIDACION_COMPARATIVA,
        )
        assert phases.index(ComparativeTablesPhase.VALIDACION_COMPARATIVA) < phases.index(
            ComparativeTablesPhase.VALIDACION_CALIDAD,
        )
        assert phases.index(ComparativeTablesPhase.VALIDACION_CALIDAD) < phases.index(
            ComparativeTablesPhase.FINALIZACION,
        )

    def test_traceability_preserved_across_full_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
        assert result.traceability_intact

    def test_source_immutability_preserved_across_full_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
        assert result.domain_model_preserved
        assert result.definitive_catalog_preserved

    def test_definitive_model_contract_prepared_for_pm7(self):
        service = ComparativeTablesService()
        service.initialize()
        result = run_full_comparative_tables_pipeline(service, process_id=uuid4())
        assert result.pm6_output_contract_valid
        assert result.pm7_input_contract_prepared
        assert result.module_certification_prepared

    def test_coordinator_controls_comparative_tables_module(self):
        config = ConfigurationProvider.default()
        coordinator = MotorCoordinator(config_provider=config)
        service = ComparativeTablesService(config_provider=config)
        service.initialize()
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()
        assert coordinator.is_module_available("comparative_tables")

    def test_states_and_events_during_full_pipeline(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComparativeTablesService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        run_full_comparative_tables_pipeline(service, process_id=process_id)

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_all_functional_pipeline_components_ready_after_initialization(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)

        functional_components = {
            "comparative_structure_engine",
            "dynamic_column_builder",
            "dynamic_row_builder",
            "provider_organization_engine",
            "group_integrity_engine",
            "traceability_metadata_engine",
            "comparative_model_builder",
            "comparative_validation_framework",
            "comparative_quality_framework",
        }
        for stage in snapshot:
            if stage.get("component_name") in functional_components:
                assert stage["component_registered"] is True
                assert stage["component_ready"] is True

    def test_central_configuration_covers_all_engines(self):
        comparative_tables = ConfigurationProvider.default().comparative_tables()
        for attr in (
            "comparative_structure_engine",
            "dynamic_column_builder",
            "dynamic_row_builder",
            "provider_organization_engine",
            "group_integrity_engine",
            "traceability_metadata_engine",
            "comparative_model_builder",
            "comparative_validation_framework",
            "comparative_quality_framework",
        ):
            assert hasattr(comparative_tables, attr)
