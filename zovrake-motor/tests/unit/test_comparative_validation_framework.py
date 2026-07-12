"""Pruebas del Comparative Validation Framework — Implementación 4.9."""

from __future__ import annotations

import copy
import importlib
import pkgutil
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.comparative_model_builder import (
    ComparativeModelBuildRequest,
    ComparativeModelBuilderEngine,
)
from zovrake_motor.comparative_tables.comparative_validation_framework import (
    ComparativeModelValidationRequest,
    ComparativeValidationFrameworkCore,
    DefinitiveCatalogAccessError,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.enums import (
    ComparativeModelValidationStatus,
    ValidationFindingSeverity,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.governance import (
    CVF_ACCEPTANCE_CRITERIA,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_model_builder import build_definitive_model_inputs


def build_definitive_catalog(
    *,
    process_id: UUID | None = None,
    extra_providers: list[str] | None = None,
    extra_commercial: dict | None = None,
) -> tuple[dict, UUID]:
    process_id = process_id or uuid4()
    enriched_catalog, integrity_report, provider_catalog, row_catalog, column_catalog, structure_catalog = (
        build_definitive_model_inputs(
            process_id=process_id,
            extra_providers=extra_providers,
            extra_commercial=extra_commercial,
        )
    )

    cmb = ComparativeModelBuilderEngine()
    cmb.initialize()
    build_result = cmb.build(
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
    return build_result.catalog.to_dict(), process_id


class TestComparativeValidationFramework:
    def test_engine_initializes_with_one_validator(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_validates_definitive_catalog_without_errors(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 1000},
        )

        result = engine.validate(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.error_count == 0
        assert result.definitive_catalog_preserved is True
        assert result.domain_model_preserved is True
        assert result.status in (
            ComparativeModelValidationStatus.VALID,
            ComparativeModelValidationStatus.PARTIAL,
        )
        assert result.validators_executed == 1
        assert result.report.comparative_quality_framework_prepared is True

    def test_detects_broken_references_without_modifying_catalog(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        broken_catalog = copy.deepcopy(definitive_catalog)
        model = broken_catalog["models"][0]
        if model.get("dynamic_rows"):
            model["dynamic_rows"][0]["column_references"] = ["NONEXISTENT-COL"]

        original_snapshot = str(definitive_catalog)

        result = engine.validate(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=broken_catalog,
            ),
        )

        assert result.error_count >= 1
        assert result.status == ComparativeModelValidationStatus.INVALID
        assert str(definitive_catalog) == original_snapshot

    def test_detects_duplicate_columns(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        duplicate_catalog = copy.deepcopy(definitive_catalog)
        model = duplicate_catalog["models"][0]
        if len(model.get("dynamic_columns", [])) >= 1:
            duplicate = copy.deepcopy(model["dynamic_columns"][0])
            model["dynamic_columns"].append(duplicate)

        result = engine.validate(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=duplicate_catalog,
            ),
        )

        assert result.error_count >= 1
        assert any(
            finding.severity == ValidationFindingSeverity.ERROR
            for check_set in result.report.check_sets
            for finding in check_set.findings
        )

    def test_preserves_definitive_catalog_without_modification(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )
        original = str(definitive_catalog)

        engine.validate(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert str(definitive_catalog) == original

    def test_rejects_unprepared_definitive_catalog(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()
        definitive_catalog, process_id = build_definitive_catalog(extra_providers=["PROV-001"])

        bad_catalog = copy.deepcopy(definitive_catalog)
        bad_catalog["comparative_validation_framework_prepared"] = False

        with pytest.raises(DefinitiveCatalogAccessError):
            engine.validate(
                ComparativeModelValidationRequest(
                    process_id=process_id,
                    definitive_catalog=bad_catalog,
                ),
            )

    def test_rejects_invalid_definitive_catalog(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()

        with pytest.raises(DefinitiveCatalogAccessError):
            engine.validate(
                ComparativeModelValidationRequest(
                    process_id=uuid4(),
                    definitive_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ComparativeValidationFrameworkCore(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().comparative_validation_framework
        assert settings.enabled is True
        assert settings.definitive_comparative_model_validator_enabled is True
        assert settings.finding_id_prefix == "CVF"
        assert settings.comparative_quality_framework_prepared is True

    def test_governance_declares_acceptance_criteria(self):
        assert "structural_completeness" in CVF_ACCEPTANCE_CRITERIA
        assert "traceability_preservation" in CVF_ACCEPTANCE_CRITERIA
        assert "contract_compliance" in CVF_ACCEPTANCE_CRITERIA

    def test_gateway_does_not_access_source_documents(self):
        engine = ComparativeValidationFrameworkCore()
        engine.initialize()

        engine_snapshot = engine.snapshot()
        assert engine_snapshot["gateway"]["accesses_source_files"] is False
        assert engine_snapshot["gateway"]["modifies_catalogs"] is False
        assert engine_snapshot["gateway"]["access_mode"] == "read_only"

    def test_package_does_not_import_forbidden_pm6_chains(self):
        package = importlib.import_module(
            "zovrake_motor.comparative_tables.comparative_validation_framework",
        )
        forbidden = (
            "canonical_representation",
            "internal_model",
            "original_document",
            "zovrake_motor.documents",
            "zovrake_motor.comprehension",
        )
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            package.__path__,
            prefix=package.__name__ + ".",
        ):
            module = importlib.import_module(modname)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            content = Path(source).read_text(encoding="utf-8")
            for term in forbidden:
                assert term not in content


class TestComparativeValidationIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = service.validate_comparative_model(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert service.comparative_validation_framework is not None
        assert service.comparative_validation_framework.report_store.count() == 1
        assert result.validators_executed == 1
        assert result.definitive_catalog_preserved is True

    def test_pipeline_registers_validation_as_next_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        cvf_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.VALIDACION_COMPARATIVA.value
        )
        assert cvf_stage["component_name"] == "comparative_validation_framework"
        assert cvf_stage["component_registered"] is True
        assert cvf_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.comparative_validation_phase()
            == ComparativeTablesPhase.VALIDACION_COMPARATIVA
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
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        service.validate_comparative_model(
            ComparativeModelValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cvf(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10
