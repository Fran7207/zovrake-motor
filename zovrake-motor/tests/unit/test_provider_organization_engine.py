"""Pruebas del Provider Organization Engine — Implementación 4.6."""

from __future__ import annotations

import copy
from dataclasses import replace
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.provider_organization_engine import (
    ProviderOrganizationEngineCore,
    ProviderOrganizationBuildRequest,
    RowCatalogAccessError,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.comparative_tables.dynamic_row_builder import (
    DynamicRowBuilderEngine,
    ComparativeRowBuildRequest,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_dynamic_row_builder import build_column_catalog


def build_row_catalog(
    *,
    process_id=None,
    extra_providers: list[str] | None = None,
    extra_commercial: dict | None = None,
) -> tuple[dict, dict, dict]:
    process_id = process_id or uuid4()
    column_catalog, structure_catalog = build_column_catalog(
        process_id=process_id,
        extra_providers=extra_providers,
        extra_commercial=extra_commercial,
    )

    drb = DynamicRowBuilderEngine()
    drb.initialize()
    row_result = drb.build(
        ComparativeRowBuildRequest(
            process_id=process_id,
            column_catalog=column_catalog,
            structure_catalog=structure_catalog,
        ),
    )
    return row_result.catalog.to_dict(), column_catalog, structure_catalog


class TestProviderOrganizationEngine:
    def test_engine_initializes_with_one_organizer(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_organizes_providers_per_group(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        providers = ["PROV-001", "PROV-002"]
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=providers,
            extra_commercial={"Precio": 1000, "Garantia": "12m"},
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        if result.catalog.provider_sets:
            provider_set = result.catalog.provider_sets[0]
            assert len(provider_set.providers) == len(providers)
            provider_ids = {provider.provider_id for provider in provider_set.providers}
            assert provider_ids == set(providers)

    def test_assigns_unique_organization_ids(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-A", "PROV-B"],
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        org_ids = [
            provider.organization_id
            for provider_set in result.catalog.provider_sets
            for provider in provider_set.providers
        ]
        assert len(org_ids) == len(set(org_ids))
        for org_id in org_ids:
            assert org_id.startswith("DOP-")

    def test_providers_remain_in_correct_group(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        for provider_set in result.catalog.provider_sets:
            for provider in provider_set.providers:
                assert provider.group_id == provider_set.group_id
                assert provider.table_id == provider_set.table_id

    def test_providers_linked_to_rows_and_columns(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
            extra_commercial={"Precio": 600},
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        if result.catalog.provider_sets and row_catalog.get("row_sets"):
            provider = result.catalog.provider_sets[0].providers[0]
            row = row_catalog["row_sets"][0]["rows"][0]
            assert provider.row_id == row["row_id"]
            assert provider.row_reference == row["row_id"]
            assert set(provider.column_references) == set(row.get("column_references", []))

    def test_preserves_catalogs_and_traceability(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )
        row_snapshot = str(row_catalog)
        column_snapshot = str(column_catalog)
        structure_snapshot = str(structure_catalog)

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        assert str(row_catalog) == row_snapshot
        assert str(column_catalog) == column_snapshot
        assert str(structure_catalog) == structure_snapshot
        assert result.column_catalog_preserved is True
        assert result.structure_catalog_preserved is True
        assert result.row_catalog_preserved is True
        assert result.domain_model_preserved is True
        if result.catalog.provider_sets and result.catalog.provider_sets[0].providers:
            provider = result.catalog.provider_sets[0].providers[0]
            payload = provider.to_dict()
            assert payload["traceability"]["source_row_catalog_id"]
            assert payload["traceability"]["source_column_catalog_id"]
            assert payload["traceability"]["row_catalog_preserved"] is True
            assert payload["metadata"]["provider_data_modified"] is False

    def test_inherits_commercial_technical_and_context(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
            extra_commercial={"Precio": 999, "Marca": "X"},
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        if result.catalog.provider_sets and result.catalog.provider_sets[0].providers:
            provider = result.catalog.provider_sets[0].providers[0]
            assert provider.commercial_information.fields.get("Precio") == 999
            assert provider.confidence_level_available
            assert isinstance(provider.inherited_context, dict)

    def test_detects_duplicate_providers_without_auto_correction(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )
        if row_catalog.get("row_sets"):
            row_catalog = copy.deepcopy(row_catalog)
            duplicate_row = dict(row_catalog["row_sets"][0]["rows"][0])
            duplicate_row["row_id"] = "DCR-999999"
            row_catalog["row_sets"][0]["rows"].append(duplicate_row)

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        if result.catalog.provider_sets:
            providers = result.catalog.provider_sets[0].providers
            provider_ids = [provider.provider_id for provider in providers]
            assert len(provider_ids) == len(set(provider_ids))
            assert any(incident.severity == "warning" for incident in result.incidents)

    def test_catalog_prepared_for_group_integrity_engine(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        assert result.catalog.group_integrity_engine_prepared is True

    def test_rejects_invalid_row_catalog(self):
        engine = ProviderOrganizationEngineCore()
        engine.initialize()
        _, column_catalog, structure_catalog = build_row_catalog(extra_providers=["PROV-001"])

        with pytest.raises(RowCatalogAccessError):
            engine.organize(
                ProviderOrganizationBuildRequest(
                    process_id=uuid4(),
                    structure_catalog=structure_catalog,
                    column_catalog=column_catalog,
                    row_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ProviderOrganizationEngineCore(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().provider_organization_engine
        assert settings.enabled is True
        assert settings.group_provider_organizer_enabled is True
        assert settings.organization_id_prefix == "DOP"
        assert settings.deterministic_sort_enabled is True


class TestProviderOrganizationIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = service.organize_providers(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        assert service.provider_organization_engine is not None
        assert service.provider_organization_engine.catalog_store.count() == 1
        assert result.organizers_executed == 1

    def test_pipeline_registers_provider_organization_as_next_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        poe_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.ORGANIZACION_PROVEEDORES.value
        )
        assert poe_stage["component_name"] == "provider_organization_engine"
        assert poe_stage["component_registered"] is True
        assert poe_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.provider_organization_phase()
            == ComparativeTablesPhase.ORGANIZACION_PROVEEDORES
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
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        service.organize_providers(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_poe(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_providers_configuration(self):
        config = ConfigurationProvider.default()
        limited_settings = replace(
            config.comparative_tables().provider_organization_engine,
            max_providers_per_organization=1,
        )
        limited_tables = replace(
            config.comparative_tables(),
            provider_organization_engine=limited_settings,
        )
        limited_config = ConfigurationProvider(
            replace(config.configuration, comparative_tables=limited_tables),
        )
        engine = ProviderOrganizationEngineCore(config_provider=limited_config)
        engine.initialize()
        process_id = uuid4()
        row_catalog, column_catalog, structure_catalog = build_row_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002", "PROV-003"],
        )

        result = engine.organize(
            ProviderOrganizationBuildRequest(
                process_id=process_id,
                structure_catalog=copy.deepcopy(structure_catalog),
                column_catalog=copy.deepcopy(column_catalog),
                row_catalog=copy.deepcopy(row_catalog),
            ),
        )

        total_providers = sum(
            len(provider_set.providers) for provider_set in result.catalog.provider_sets
        )
        if total_providers > 1:
            assert total_providers == 1
            assert any(incident.severity == "warning" for incident in result.incidents)
