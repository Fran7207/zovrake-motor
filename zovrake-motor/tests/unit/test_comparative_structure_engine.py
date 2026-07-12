"""Pruebas del Comparative Structure Engine — Implementación 4.2."""

from __future__ import annotations

import copy
from dataclasses import replace
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.comparative_structure_engine import (
    ComparativeStructureBuilderEngine,
    ComparativeStructureBuildRequest,
    DomainModelCatalogAccessError,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_domain_model import build_context_association_catalog
from zovrake_motor.classification.comparative_domain_model import (
    ComparativeDomainModelBuilderEngine,
    ComparativeDomainModelBuildRequest,
)


def build_domain_model_catalog(*, process_id=None) -> dict:
    process_id = process_id or uuid4()
    context_catalog = build_context_association_catalog(process_id=process_id)
    cdmb = ComparativeDomainModelBuilderEngine()
    cdmb.initialize()
    return cdmb.build(
        ComparativeDomainModelBuildRequest(
            process_id=process_id,
            context_association_catalog=context_catalog,
        ),
    ).catalog.to_dict()


class TestComparativeStructureBuilderEngine:
    def test_engine_initializes_with_one_builder(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_one_structure_per_domain_group(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        result = engine.build(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        models_count = len(catalog_dict.get("models", []))
        if models_count:
            assert len(result.catalog.structures) == models_count
            structure = result.catalog.structures[0]
            assert structure.table_id.startswith("CTS-")
            assert structure.internal_table_id.startswith("cse://")
            assert structure.group_id
            assert structure.group_type
            assert structure.columns_prepared == ()
            assert structure.rows_prepared == ()
            assert structure.providers_prepared == ()

    def test_assigns_unique_table_ids(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        result = engine.build(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        table_ids = [structure.table_id for structure in result.catalog.structures]
        assert len(table_ids) == len(set(table_ids))
        for table_id in table_ids:
            assert table_id.startswith("CTS-")
            parts = table_id.split("-", 1)
            assert len(parts) == 2
            assert parts[1].isdigit()
            assert len(parts[1]) == 6

    def test_preserves_domain_model_and_traceability(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)
        original_snapshot = str(catalog_dict)

        result = engine.build(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot
        assert result.domain_model_preserved is True
        if result.catalog.structures:
            structure = result.catalog.structures[0]
            payload = structure.to_dict()
            assert payload["traceability"]["source_domain_catalog_id"]
            assert payload["traceability"]["source_comparative_model_id"]
            assert payload["traceability"]["domain_model_preserved"] is True
            assert payload["domain_reference"]["comparative_model_id"]

    def test_structures_are_independent(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        result = engine.build(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        if len(result.catalog.structures) >= 2:
            first = result.catalog.structures[0]
            second = result.catalog.structures[1]
            assert first.table_id != second.table_id
            assert first.group_id != second.group_id or first.domain_reference.comparative_model_id != (
                second.domain_reference.comparative_model_id
            )

    def test_catalog_prepared_for_downstream_builders(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        result = engine.build(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        catalog = result.catalog
        assert catalog.dynamic_column_builder_prepared is True
        assert catalog.dynamic_row_builder_prepared is True
        assert catalog.domain_model_preserved is True

    def test_rejects_invalid_domain_model_catalog(self):
        engine = ComparativeStructureBuilderEngine()
        engine.initialize()

        with pytest.raises(DomainModelCatalogAccessError):
            engine.build(
                ComparativeStructureBuildRequest(
                    process_id=uuid4(),
                    domain_model_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ComparativeStructureBuilderEngine(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().comparative_structure_engine
        assert settings.enabled is True
        assert settings.domain_model_group_structure_builder_enabled is True
        assert settings.structure_id_prefix == "CTS"
        assert settings.structure_id_immutable is True


class TestComparativeStructureEngineIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        result = service.build_comparative_structure(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        assert service.comparative_structure_engine is not None
        assert service.comparative_structure_engine.catalog_store.count() == 1
        assert result.builders_executed == 1

    def test_pipeline_registers_structure_as_first_functional_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        structure_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.ESTRUCTURA_COMPARATIVA.value
        )
        assert structure_stage["component_name"] == "comparative_structure_engine"
        assert structure_stage["component_registered"] is True
        assert structure_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.comparative_structure_phase()
            == ComparativeTablesPhase.ESTRUCTURA_COMPARATIVA
        )

    def test_records_state_and_events(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComparativeTablesService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        service.build_comparative_structure(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=catalog_dict,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cse(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_structures_configuration(self):
        config = ConfigurationProvider.default()
        limited_settings = replace(
            config.comparative_tables().comparative_structure_engine,
            max_structures_per_process=1,
        )
        limited_tables = replace(
            config.comparative_tables(),
            comparative_structure_engine=limited_settings,
        )
        limited_config = ConfigurationProvider(
            replace(config.configuration, comparative_tables=limited_tables),
        )
        engine = ComparativeStructureBuilderEngine(config_provider=limited_config)
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_domain_model_catalog(process_id=process_id)

        result = engine.build(
            ComparativeStructureBuildRequest(
                process_id=process_id,
                domain_model_catalog=copy.deepcopy(catalog_dict),
            ),
        )

        if len(catalog_dict.get("models", [])) > 1:
            assert len(result.catalog.structures) == 1
            assert any(incident.severity == "warning" for incident in result.incidents)
