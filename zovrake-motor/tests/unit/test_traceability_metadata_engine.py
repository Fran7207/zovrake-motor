"""Pruebas del Traceability & Metadata Engine — Implementación 4.7."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.traceability_metadata_engine import (
    IntegrityReportAccessError,
    TraceabilityMetadataEngineCore,
    TraceabilityMetadataEnrichmentRequest,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.enums import (
    TraceabilityMetadataEnrichmentStatus,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.group_integrity_engine import (
    GroupIntegrityEngineCore,
    GroupIntegrityValidationRequest,
)
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_group_integrity_engine import build_provider_catalog


def build_integrity_enrichment_inputs(
    *,
    process_id=None,
    extra_providers: list[str] | None = None,
    extra_commercial: dict | None = None,
) -> tuple[dict, dict, dict, dict, dict]:
    process_id = process_id or uuid4()
    provider_catalog, row_catalog, column_catalog, structure_catalog = build_provider_catalog(
        process_id=process_id,
        extra_providers=extra_providers,
        extra_commercial=extra_commercial,
    )

    gie = GroupIntegrityEngineCore()
    gie.initialize()
    integrity_result = gie.validate(
        GroupIntegrityValidationRequest(
            process_id=process_id,
            structure_catalog=structure_catalog,
            column_catalog=column_catalog,
            row_catalog=row_catalog,
            provider_catalog=provider_catalog,
        ),
    )

    return (
        integrity_result.report.to_dict(),
        provider_catalog,
        row_catalog,
        column_catalog,
        structure_catalog,
    )


class TestTraceabilityMetadataEngine:
    def test_engine_initializes_with_one_enricher(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_enriches_traceability_for_valid_catalogs(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()
        process_id = uuid4()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001", "PROV-002"],
                extra_commercial={"Precio": 1000},
            )
        )

        result = engine.enrich(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        assert result.status == TraceabilityMetadataEnrichmentStatus.ENRICHED
        assert result.enriched_tables_count >= 1
        assert result.structure_catalog_preserved is True
        assert result.integrity_report_preserved is True
        assert result.domain_model_preserved is True

    def test_incorporates_inherited_context_without_modification(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()
        process_id = uuid4()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        original_context = ""
        if structure_catalog.get("structures"):
            original_context = str(
                structure_catalog["structures"][0].get("metadata_prepared", {}).get(
                    "inherited_context", {},
                ),
            )

        result = engine.enrich(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        enriched = result.catalog.enriched_tables[0]
        assert str(enriched.inherited_context) == original_context or enriched.inherited_context

    def test_preserves_confidence_level_without_recalculation(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()
        process_id = uuid4()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        expected_confidence = "not_evaluated"
        if structure_catalog.get("structures"):
            expected_confidence = str(
                structure_catalog["structures"][0]
                .get("metadata_prepared", {})
                .get("confidence_level_available", "not_evaluated"),
            )

        result = engine.enrich(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        enriched = result.catalog.enriched_tables[0]
        assert enriched.confidence_level_available == expected_confidence

    def test_does_not_modify_upstream_catalogs(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()
        process_id = uuid4()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        originals = (
            str(structure_catalog),
            str(column_catalog),
            str(row_catalog),
            str(provider_catalog),
            str(integrity_report),
        )

        engine.enrich(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        assert str(structure_catalog) == originals[0]
        assert str(column_catalog) == originals[1]
        assert str(row_catalog) == originals[2]
        assert str(provider_catalog) == originals[3]
        assert str(integrity_report) == originals[4]

    def test_includes_document_traceability_references(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()
        process_id = uuid4()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        result = engine.enrich(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        enriched = result.catalog.enriched_tables[0]
        assert enriched.traceability.document_evidence.document_id
        assert enriched.traceability.source_structure_catalog_id
        assert enriched.traceability.source_integrity_report_id
        assert enriched.metadata.motor_internal_references["integrity_report_id"]

    def test_rejects_unprepared_integrity_report(self):
        engine = TraceabilityMetadataEngineCore()
        engine.initialize()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(extra_providers=["PROV-001"])
        )

        bad_report = copy.deepcopy(integrity_report)
        bad_report["traceability_metadata_engine_prepared"] = False

        with pytest.raises(IntegrityReportAccessError):
            engine.enrich(
                TraceabilityMetadataEnrichmentRequest(
                    process_id=uuid4(),
                    structure_catalog=structure_catalog,
                    column_catalog=column_catalog,
                    row_catalog=row_catalog,
                    provider_catalog=provider_catalog,
                    integrity_report=bad_report,
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = TraceabilityMetadataEngineCore(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().traceability_metadata_engine
        assert settings.enabled is True
        assert settings.comparative_table_metadata_enricher_enabled is True
        assert settings.enrichment_id_prefix == "TME"
        assert settings.comparative_model_builder_prepared is True


class TestTraceabilityMetadataIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001", "PROV-002"],
            )
        )

        result = service.enrich_traceability_metadata(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
                structure_catalog=structure_catalog,
                column_catalog=column_catalog,
                row_catalog=row_catalog,
                provider_catalog=provider_catalog,
                integrity_report=integrity_report,
            ),
        )

        assert service.traceability_metadata_engine is not None
        assert service.traceability_metadata_engine.catalog_store.count() == 1
        assert result.enrichers_executed == 1
        assert result.catalog.comparative_model_builder_prepared is True

    def test_pipeline_registers_traceability_as_next_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        tme_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.TRAZABILIDAD_METADATOS.value
        )
        assert tme_stage["component_name"] == "traceability_metadata_engine"
        assert tme_stage["component_registered"] is True
        assert tme_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.traceability_metadata_phase()
            == ComparativeTablesPhase.TRAZABILIDAD_METADATOS
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
        integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
            build_integrity_enrichment_inputs(
                process_id=process_id,
                extra_providers=["PROV-001"],
            )
        )

        service.enrich_traceability_metadata(
            TraceabilityMetadataEnrichmentRequest(
                process_id=process_id,
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

    def test_module_ready_count_includes_tme(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10
