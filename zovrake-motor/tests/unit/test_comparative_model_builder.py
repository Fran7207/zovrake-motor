"""Pruebas del Comparative Model Builder — Implementación 4.8."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.comparative_model_builder import (
    ComparativeModelBuilderEngine,
    ComparativeModelBuildRequest,
    EnrichedCatalogAccessError,
    PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.comparative_tables.comparative_model_builder.enums import (
    ComparativeModelBuildStatus,
)
from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.comparative_tables.traceability_metadata_engine import (
    TraceabilityMetadataEngineCore,
    TraceabilityMetadataEnrichmentRequest,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_traceability_metadata_engine import build_integrity_enrichment_inputs


def build_definitive_model_inputs(
    *,
    process_id=None,
    extra_providers: list[str] | None = None,
    extra_commercial: dict | None = None,
) -> tuple[dict, dict, dict, dict, dict, dict]:
    process_id = process_id or uuid4()
    integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
        build_integrity_enrichment_inputs(
            process_id=process_id,
            extra_providers=extra_providers,
            extra_commercial=extra_commercial,
        )
    )

    tme = TraceabilityMetadataEngineCore()
    tme.initialize()
    enrichment_result = tme.enrich(
        TraceabilityMetadataEnrichmentRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
            provider_catalog=provider_catalog,
            integrity_report=integrity_report,
        ),
    )

    return (
        enrichment_result.catalog.to_dict(),
        integrity_report,
        provider_catalog,
        row_catalog,
        column_catalog,
        structure_catalog,
    )


class TestComparativeModelBuilder:
    def test_engine_initializes_with_one_builder(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_one_definitive_model_per_group(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(
                process_id=process_id,
                extra_providers=["PROV-001", "PROV-002"],
                extra_commercial={"Precio": 1000},
            )
        )

        result = engine.build(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        enriched_count = len(enriched_catalog.get("enriched_tables", []))
        assert result.status == ComparativeModelBuildStatus.BUILT
        assert result.models_built_count == enriched_count
        assert len(result.catalog.models) == enriched_count
        assert result.catalog.pm6_definitive_output_contract is True
        assert result.catalog.pm7_input_contract_prepared is True

    def test_definitive_model_contains_required_contract_fields(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        result = engine.build(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        model = result.catalog.models[0]
        model_dict = model.to_dict()
        for field in PM6_DEFINITIVE_MODEL_REQUIRED_FIELDS:
            assert field in model_dict

        assert model.definitive_model_id.startswith("CMD-")
        assert model.comparative_table_id
        assert model.group_id
        assert model.inherited_context is not None
        assert model.confidence_level_available
        assert model.traceability

    def test_preserves_upstream_catalogs_without_modification(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        originals = (
            str(enriched_catalog),
            str(structure_catalog),
            str(column_catalog),
            str(row_catalog),
            str(provider_catalog),
            str(integrity_report),
        )

        engine.build(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        assert str(enriched_catalog) == originals[0]
        assert str(structure_catalog) == originals[1]
        assert str(column_catalog) == originals[2]
        assert str(row_catalog) == originals[3]
        assert str(provider_catalog) == originals[4]
        assert str(integrity_report) == originals[5]

    def test_includes_commercial_and_technical_information(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
                extra_commercial={"Precio": 2500},
            )
        )

        result = engine.build(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        model = result.catalog.models[0]
        assert isinstance(model.commercial_information.fields, dict)
        assert isinstance(model.technical_information.fields, dict)
        assert len(model.dynamic_columns) >= 1
        assert len(model.dynamic_rows) >= 1
        assert len(model.provider_organization) >= 1

    def test_rejects_unprepared_enriched_catalog(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(extra_providers=["PROV-001"])
        )

        bad_catalog = copy.deepcopy(enriched_catalog)
        bad_catalog["comparative_model_builder_prepared"] = False

        with pytest.raises(EnrichedCatalogAccessError):
            engine.build(
                ComparativeModelBuildRequest(
                    process_id=uuid4(),
                    enriched_catalog=bad_catalog,
                    structure_catalog=structure_catalog,
                    column_catalog=column_catalog,
                    row_catalog=row_catalog,
                    provider_catalog=provider_catalog,
                    integrity_report=integrity_report,
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ComparativeModelBuilderEngine(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().comparative_model_builder
        assert settings.enabled is True
        assert settings.group_comparative_model_builder_enabled is True
        assert settings.definitive_model_id_prefix == "CMD"
        assert settings.comparative_validation_framework_prepared is True

    def test_catalog_declares_pm6_official_contract(self):
        engine = ComparativeModelBuilderEngine()
        engine.initialize()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(extra_providers=["PROV-001"])
        )

        result = engine.build(
            ComparativeModelBuildRequest(
                process_id=uuid4(),
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        assert PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME == "DefinitiveComparativeModelCatalog"
        assert result.catalog.catalog_id.startswith("cmb-catalog://")
        assert result.catalog.comparative_validation_framework_prepared is True


class TestComparativeModelBuilderIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(
                process_id=process_id,
                extra_providers=["PROV-001", "PROV-002"],
            )
        )

        result = service.build_comparative_model(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        assert service.comparative_model_builder is not None
        assert service.comparative_model_builder.catalog_store.count() == 1
        assert result.builders_executed == 1

    def test_pipeline_registers_model_build_as_next_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        cmb_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.MODELO_COMPARATIVO.value
        )
        assert cmb_stage["component_name"] == "comparative_model_builder"
        assert cmb_stage["component_registered"] is True
        assert cmb_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.comparative_model_build_phase()
            == ComparativeTablesPhase.MODELO_COMPARATIVO
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
        enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_definitive_model_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        service.build_comparative_model(
            ComparativeModelBuildRequest(
                process_id=process_id,
                enriched_catalog=enriched_catalog,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cmb(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10
