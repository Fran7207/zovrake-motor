"""Pruebas del Group Integrity Engine — Implementación 4.6."""

from __future__ import annotations

import copy
from dataclasses import replace
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.group_integrity_engine import (
    GroupIntegrityEngineCore,
    GroupIntegrityValidationRequest,
    ProviderCatalogAccessError,
)
from zovrake_motor.comparative_tables.group_integrity_engine.enums import (
    GroupIntegrityValidationStatus,
    IntegrityFindingSeverity,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.comparative_tables.provider_organization_engine import (
    ProviderOrganizationEngineCore,
    ProviderOrganizationBuildRequest,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_provider_organization_engine import build_row_catalog


def build_provider_catalog(
    *,
    process_id=None,
    extra_providers: list[str] | None = None,
    extra_commercial: dict | None = None,
) -> tuple[dict, dict, dict, dict]:
    process_id = process_id or uuid4()
    row_catalog, column_catalog, structure_catalog = build_row_catalog(
        process_id=process_id,
        extra_providers=extra_providers,
        extra_commercial=extra_commercial,
    )

    poe = ProviderOrganizationEngineCore()
    poe.initialize()
    provider_result = poe.organize(
        ProviderOrganizationBuildRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
        ),
    )
    return (
        provider_result.catalog.to_dict(),
        row_catalog,
        column_catalog,
        structure_catalog,
    )


class TestGroupIntegrityEngine:
    def test_engine_initializes_with_one_validator(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_validates_integrity_for_valid_catalogs(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()
        process_id = uuid4()
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 1000},
        )

        result = engine.validate(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        assert result.status == GroupIntegrityValidationStatus.VALID
        assert result.error_count == 0
        assert result.structure_catalog_preserved is True
        assert result.provider_catalog_preserved is True

    def test_detects_duplicate_providers_without_modifying_catalogs(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()
        process_id = uuid4()
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        if provider_catalog.get("provider_sets"):
            provider_catalog = copy.deepcopy(provider_catalog)
            duplicate = dict(provider_catalog["provider_sets"][0]["providers"][0])
            duplicate["organization_id"] = "DOP-999999"
            provider_catalog["provider_sets"][0]["providers"].append(duplicate)

        original = str(provider_catalog)
        result = engine.validate(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        assert str(provider_catalog) == original
        assert result.status == GroupIntegrityValidationStatus.INVALID
        assert result.error_count >= 1
        assert result.provider_catalog_preserved is True

    def test_detects_broken_row_column_references(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()
        process_id = uuid4()
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        if row_catalog.get("row_sets"):
            row_catalog = copy.deepcopy(row_catalog)
            row_catalog["row_sets"][0]["rows"][0]["column_references"] = ["DCC-INVALID"]

        result = engine.validate(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        assert result.status == GroupIntegrityValidationStatus.INVALID
        assert result.error_count >= 1

    def test_preserves_traceability_in_report(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()
        process_id = uuid4()
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        result = engine.validate(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        assert result.report.traceability.source_structure_catalog_id
        assert result.report.traceability.source_provider_catalog_id
        assert result.report.traceability_metadata_engine_prepared is True
        assert result.domain_model_preserved is True

    def test_validates_providers_belong_to_correct_group(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()
        process_id = uuid4()
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        if provider_catalog.get("provider_sets"):
            provider_catalog = copy.deepcopy(provider_catalog)
            provider_catalog["provider_sets"][0]["providers"][0]["group_id"] = "WRONG-GROUP"

        result = engine.validate(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        assert result.error_count >= 1
        assert any(
            finding.severity == IntegrityFindingSeverity.ERROR
            for check_set in result.report.check_sets
            for finding in check_set.findings
        )

    def test_rejects_invalid_provider_catalog(self):
        engine = GroupIntegrityEngineCore()
        engine.initialize()
        _, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            extra_providers=["PROV-001"],
        )

        with pytest.raises(ProviderCatalogAccessError):
            engine.validate(
                GroupIntegrityValidationRequest(
                    process_id=uuid4(),
                    structure_catalog=structure_catalog,
                    column_catalog=column_catalog,
                    row_catalog=row_catalog,
                    provider_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = GroupIntegrityEngineCore(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().group_integrity_engine
        assert settings.enabled is True
        assert settings.comparative_table_integrity_validator_enabled is True
        assert settings.finding_id_prefix == "GIC"


class TestGroupIntegrityIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = service.validate_group_integrity(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        assert service.group_integrity_engine is not None
        assert service.group_integrity_engine.report_store.count() == 1
        assert result.validators_executed == 1

    def test_pipeline_registers_integrity_as_next_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        gie_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.INTEGRIDAD_GRUPOS.value
        )
        assert gie_stage["component_name"] == "group_integrity_engine"
        assert gie_stage["component_registered"] is True
        assert gie_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.group_integrity_phase()
            == ComparativeTablesPhase.INTEGRIDAD_GRUPOS
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
        provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        service.validate_group_integrity(
            GroupIntegrityValidationRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_gie(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10
