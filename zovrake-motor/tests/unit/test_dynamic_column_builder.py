"""Pruebas del Dynamic Column Builder — Implementación 4.3."""

from __future__ import annotations

import copy
from dataclasses import replace
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.dynamic_column_builder import (
    DynamicColumnBuilderEngine,
    ComparativeColumnBuildRequest,
    StructureCatalogAccessError,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_structure_engine import build_domain_model_catalog
from zovrake_motor.comparative_tables.comparative_structure_engine import (
    ComparativeStructureBuilderEngine,
    ComparativeStructureBuildRequest,
)


def build_structure_catalog(*, process_id=None, extra_commercial: dict | None = None) -> dict:
    process_id = process_id or uuid4()
    domain_catalog = build_domain_model_catalog(process_id=process_id)

    if extra_commercial and domain_catalog.get("models"):
        model = dict(domain_catalog["models"][0])
        commercial = dict(model.get("commercial_information", {}).get("fields", {}))
        commercial.update(extra_commercial)
        model["commercial_information"] = {"fields": commercial}
        domain_catalog = dict(domain_catalog)
        domain_catalog["models"] = [model, *domain_catalog["models"][1:]]

    cse = ComparativeStructureBuilderEngine()
    cse.initialize()
    return cse.build(
        ComparativeStructureBuildRequest(
            process_id=process_id,
            domain_model_catalog=domain_catalog,
        ),
    ).catalog.to_dict()


class TestDynamicColumnBuilderEngine:
    def test_engine_initializes_with_one_builder(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_dynamic_columns_per_structure(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(
            process_id=process_id,
            extra_commercial={
                "Precio": 1000,
                "Tiempo de entrega": "15 dias",
                "Garantia": "12 meses",
            },
        )

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        structures_count = len(structure_catalog.get("structures", []))
        if structures_count:
            assert len(result.catalog.column_sets) == structures_count
            column_set = result.catalog.column_sets[0]
            attribute_names = {column.attribute_name for column in column_set.columns}
            assert "Precio" in attribute_names
            assert "Tiempo de entrega" in attribute_names
            assert "Garantia" in attribute_names

    def test_assigns_unique_column_ids(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(process_id=process_id)

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        column_ids = [
            column.column_id
            for column_set in result.catalog.column_sets
            for column in column_set.columns
        ]
        assert len(column_ids) == len(set(column_ids))
        for column_id in column_ids:
            assert column_id.startswith("DCC-")

    def test_no_duplicate_columns_within_group(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(
            process_id=process_id,
            extra_commercial={"Precio": 100, "precio": 200},
        )

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        if result.catalog.column_sets:
            names = [column.attribute_name.lower() for column in result.catalog.column_sets[0].columns]
            assert len(names) == len(set(names))

    def test_preserves_structure_catalog_and_traceability(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(process_id=process_id)
        original_snapshot = str(structure_catalog)

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        assert str(structure_catalog) == original_snapshot
        assert result.structure_catalog_preserved is True
        assert result.domain_model_preserved is True
        if result.catalog.column_sets and result.catalog.column_sets[0].columns:
            column = result.catalog.column_sets[0].columns[0]
            payload = column.to_dict()
            assert payload["traceability"]["source_structure_catalog_id"]
            assert payload["traceability"]["source_table_id"]
            assert payload["traceability"]["structure_catalog_preserved"] is True

    def test_columns_are_independent_between_groups(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(
            process_id=process_id,
            extra_commercial={"Precio": 100},
        )

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        if len(result.catalog.column_sets) >= 2:
            first_group = result.catalog.column_sets[0].group_id
            second_group = result.catalog.column_sets[1].group_id
            assert first_group != second_group
            for column_set in result.catalog.column_sets:
                for column in column_set.columns:
                    assert column.group_id == column_set.group_id

    def test_catalog_prepared_for_dynamic_row_builder(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(process_id=process_id)

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        assert result.catalog.dynamic_row_builder_prepared is True

    def test_rejects_invalid_structure_catalog(self):
        engine = DynamicColumnBuilderEngine()
        engine.initialize()

        with pytest.raises(StructureCatalogAccessError):
            engine.build(
                ComparativeColumnBuildRequest(
                    process_id=uuid4(),
                    structure_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = DynamicColumnBuilderEngine(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().dynamic_column_builder
        assert settings.enabled is True
        assert settings.structure_attribute_column_builder_enabled is True
        assert settings.column_id_prefix == "DCC"
        assert settings.column_id_immutable is True


class TestDynamicColumnBuilderIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(process_id=process_id)

        result = service.build_dynamic_columns(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        assert service.dynamic_column_builder is not None
        assert service.dynamic_column_builder.catalog_store.count() == 1
        assert result.builders_executed == 1

    def test_pipeline_registers_column_build_as_next_functional_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        column_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.CONSTRUCCION_COLUMNAS.value
        )
        assert column_stage["component_name"] == "dynamic_column_builder"
        assert column_stage["component_registered"] is True
        assert column_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.dynamic_column_build_phase()
            == ComparativeTablesPhase.CONSTRUCCION_COLUMNAS
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
        structure_catalog = build_structure_catalog(process_id=process_id)

        service.build_dynamic_columns(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_dcb(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_columns_configuration(self):
        config = ConfigurationProvider.default()
        limited_settings = replace(
            config.comparative_tables().dynamic_column_builder,
            max_columns_per_process=1,
        )
        limited_tables = replace(
            config.comparative_tables(),
            dynamic_column_builder=limited_settings,
        )
        limited_config = ConfigurationProvider(
            replace(config.configuration, comparative_tables=limited_tables),
        )
        engine = DynamicColumnBuilderEngine(config_provider=limited_config)
        engine.initialize()
        process_id = uuid4()
        structure_catalog = build_structure_catalog(
            process_id=process_id,
            extra_commercial={"Precio": 1, "Garantia": "12m", "Marca": "X"},
        )

        result = engine.build(
            ComparativeColumnBuildRequest(
                process_id=process_id,
                structure_catalog=copy.deepcopy(structure_catalog),
            ),
        )

        total_columns = sum(len(column_set.columns) for column_set in result.catalog.column_sets)
        if total_columns > 1:
            assert total_columns == 1
            assert any(incident.severity == "warning" for incident in result.incidents)


def test_extracts_union_of_source_item_attributes():
    from zovrake_motor.comparative_tables.dynamic_column_builder.builders import (
        extract_attribute_candidates,
    )

    candidates = extract_attribute_candidates(
        {"commercial": {}},
        {},
        {
            "c1": {
                "description": "Cemento Portland Tipo I",
                "quantity": "100",
                "unit": "BLS",
                "unit_price": "32.00",
                "fields": {"marca": "A", "presentacion": "42.5 KG"},
            },
            "c2": {
                "description": "Cemento Portland Tipo I",
                "quantity": "120",
                "unit": "BLS",
                "unit_price": "30.00",
                "fields": {"marca": "B", "certificado": "ISO"},
            },
        },
    )

    names = [name.casefold() for name, *_ in candidates]
    assert "descripción" in names
    assert "cantidad" in names
    assert "unidad" in names
    assert "precio unitario" in names
    assert "marca" in names
    assert "presentacion" in names
    assert "certificado" in names


def test_does_not_override_existing_structured_attributes():
    from zovrake_motor.comparative_tables.dynamic_column_builder.builders import (
        extract_attribute_candidates,
    )

    candidates = extract_attribute_candidates(
        {"commercial": {"Cantidad": "100"}},
        {},
        {
            "c1": {"quantity": "100", "fields": {"marca": "A"}},
        },
    )

    normalized = [name.casefold() for name, *_ in candidates]
    assert normalized.count("cantidad") == 1
    assert "marca" in normalized
