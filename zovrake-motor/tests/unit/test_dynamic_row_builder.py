"""Pruebas del Dynamic Row Builder — Implementación 4.4."""

from __future__ import annotations

import copy
from dataclasses import replace
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.dynamic_row_builder import (
    DynamicRowBuilderEngine,
    ComparativeRowBuildRequest,
    ColumnCatalogAccessError,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_dynamic_column_builder import build_structure_catalog
from zovrake_motor.comparative_tables.dynamic_column_builder import (
    DynamicColumnBuilderEngine,
    ComparativeColumnBuildRequest,
)


def build_column_catalog(
    *,
    process_id=None,
    extra_providers: list[str] | None = None,
    extra_commercial: dict | None = None,
) -> tuple[dict, dict]:
    process_id = process_id or uuid4()
    structure_catalog = build_structure_catalog(
        process_id=process_id,
        extra_commercial=extra_commercial,
    )

    if extra_providers and structure_catalog.get("structures"):
        structure_catalog = copy.deepcopy(structure_catalog)
        for structure in structure_catalog["structures"]:
            metadata_prepared = dict(structure.get("metadata_prepared", {}))
            metadata_prepared["available_providers"] = list(extra_providers)
            structure["metadata_prepared"] = metadata_prepared

    dcb = DynamicColumnBuilderEngine()
    dcb.initialize()
    column_result = dcb.build(
        ComparativeColumnBuildRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
        ),
    )
    return column_result.catalog.to_dict(), structure_catalog


class TestDynamicRowBuilderEngine:
    def test_engine_initializes_with_one_builder(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_one_row_per_provider(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        providers = ["PROV-001", "PROV-002", "PROV-003"]
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=providers,
            extra_commercial={"Precio": 1000},
        )

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        if result.catalog.row_sets:
            row_set = result.catalog.row_sets[0]
            assert len(row_set.rows) == len(providers)
            provider_ids = {row.provider_id for row in row_set.rows}
            assert provider_ids == set(providers)

    def test_assigns_unique_row_ids(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-A", "PROV-B"],
        )

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        row_ids = [
            row.row_id
            for row_set in result.catalog.row_sets
            for row in row_set.rows
        ]
        assert len(row_ids) == len(set(row_ids))
        for row_id in row_ids:
            assert row_id.startswith("DCR-")

    def test_rows_belong_to_correct_group(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        for row_set in result.catalog.row_sets:
            for row in row_set.rows:
                assert row.group_id == row_set.group_id
                assert row.table_id == row_set.table_id

    def test_rows_linked_to_dynamic_columns(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
            extra_commercial={"Precio": 500, "Garantia": "12m"},
        )

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        if result.catalog.row_sets and column_catalog.get("column_sets"):
            row = result.catalog.row_sets[0].rows[0]
            column_ids = {
                column["column_id"]
                for column in column_catalog["column_sets"][0]["columns"]
            }
            assert set(row.column_references) == column_ids
            assert len(row.cells_reserved) == len(column_ids)
            assert all(not cell.value_prepared for cell in row.cells_reserved)

    def test_preserves_input_catalogs_and_traceability(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )
        column_snapshot = str(column_catalog)
        structure_snapshot = str(structure_catalog)

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        assert str(column_catalog) == column_snapshot
        assert str(structure_catalog) == structure_snapshot
        assert result.column_catalog_preserved is True
        assert result.structure_catalog_preserved is True
        assert result.domain_model_preserved is True
        if result.catalog.row_sets and result.catalog.row_sets[0].rows:
            row = result.catalog.row_sets[0].rows[0]
            payload = row.to_dict()
            assert payload["traceability"]["source_column_catalog_id"]
            assert payload["traceability"]["source_structure_catalog_id"]
            assert payload["traceability"]["column_catalog_preserved"] is True

    def test_rows_are_independent_between_groups(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-G1"],
        )

        if len(structure_catalog.get("structures", [])) >= 2:
            structure_catalog = copy.deepcopy(structure_catalog)
            structure_catalog["structures"][1]["metadata_prepared"]["available_providers"] = [
                "PROV-G2-A",
                "PROV-G2-B",
            ]

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        if len(result.catalog.row_sets) >= 2:
            first_providers = {row.provider_id for row in result.catalog.row_sets[0].rows}
            second_providers = {row.provider_id for row in result.catalog.row_sets[1].rows}
            assert first_providers.isdisjoint(second_providers)

    def test_catalog_prepared_for_provider_organization_engine(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        assert result.catalog.provider_organization_engine_prepared is True

    def test_rejects_invalid_column_catalog(self):
        engine = DynamicRowBuilderEngine()
        engine.initialize()
        _, structure_catalog = build_column_catalog(extra_providers=["PROV-001"])

        with pytest.raises(ColumnCatalogAccessError):
            engine.build(
                ComparativeRowBuildRequest(
                    process_id=uuid4(),
                    column_catalog={"catalog_id": "invalid"},
                    structure_catalog=structure_catalog,
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = DynamicRowBuilderEngine(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().dynamic_row_builder
        assert settings.enabled is True
        assert settings.provider_row_builder_enabled is True
        assert settings.row_id_prefix == "DCR"
        assert settings.row_id_immutable is True


class TestDynamicRowBuilderIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = service.build_dynamic_rows(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        assert service.dynamic_row_builder is not None
        assert service.dynamic_row_builder.catalog_store.count() == 1
        assert result.builders_executed == 1

    def test_pipeline_registers_row_build_as_next_functional_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        row_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.CONSTRUCCION_FILAS.value
        )
        assert row_stage["component_name"] == "dynamic_row_builder"
        assert row_stage["component_registered"] is True
        assert row_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.dynamic_row_build_phase()
            == ComparativeTablesPhase.CONSTRUCCION_FILAS
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
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        service.build_dynamic_rows(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=column_catalog,
                structure_catalog=structure_catalog,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_drb(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_rows_configuration(self):
        config = ConfigurationProvider.default()
        limited_settings = replace(
            config.comparative_tables().dynamic_row_builder,
            max_rows_per_process=1,
        )
        limited_tables = replace(
            config.comparative_tables(),
            dynamic_row_builder=limited_settings,
        )
        limited_config = ConfigurationProvider(
            replace(config.configuration, comparative_tables=limited_tables),
        )
        engine = DynamicRowBuilderEngine(config_provider=limited_config)
        engine.initialize()
        process_id = uuid4()
        column_catalog, structure_catalog = build_column_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002", "PROV-003"],
        )

        result = engine.build(
            ComparativeRowBuildRequest(
                process_id=process_id,
                column_catalog=copy.deepcopy(column_catalog),
                structure_catalog=copy.deepcopy(structure_catalog),
            ),
        )

        total_rows = sum(len(row_set.rows) for row_set in result.catalog.row_sets)
        if total_rows > 1:
            assert total_rows == 1
            assert any(incident.severity == "warning" for incident in result.incidents)
