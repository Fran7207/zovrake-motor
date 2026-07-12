"""Pruebas del Comparative Quality Framework — Implementación 4.10."""

from __future__ import annotations

import copy
import importlib
import pkgutil
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from zovrake_motor import ComparativeTablesService
from zovrake_motor.comparative_tables.comparative_quality_framework import (
    ComparativeQualityFrameworkCore,
    ComparativeQualityInputAccessError,
    ComparativeQualityValidationRequest,
    ComparativeQualityValidationStatus,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.governance import (
    CQF_ACCEPTANCE_CRITERIA,
)
from zovrake_motor.comparative_tables.comparative_validation_framework import (
    ComparativeModelValidationRequest,
    ComparativeValidationFrameworkCore,
)
from zovrake_motor.comparative_tables.enums import ComparativeTablesPhase
from zovrake_motor.comparative_tables.pipeline import ComparativeTablesPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_validation_framework import build_definitive_catalog


def build_quality_audit_inputs(
    *,
    process_id: UUID | None = None,
    extra_providers: list[str] | None = None,
) -> tuple[dict, dict, UUID]:
    process_id = process_id or uuid4()
    definitive_catalog, _ = build_definitive_catalog(
        process_id=process_id,
        extra_providers=extra_providers,
    )

    cvf = ComparativeValidationFrameworkCore()
    cvf.initialize()
    validation_result = cvf.validate(
        ComparativeModelValidationRequest(
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        ),
    )

    return definitive_catalog, validation_result.report.to_dict(), process_id


class TestComparativeQualityFramework:
    def test_engine_initializes_with_six_validators(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 6

    def test_audits_definitive_catalog_and_validation_report(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = engine.audit(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_report,
            ),
        )

        assert result.report.checks_executed > 0
        assert result.definitive_catalog_preserved is True
        assert result.validation_report_preserved is True
        assert result.report.checks_passed > 0

    def test_preserves_source_data_without_modification(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )
        catalog_snapshot = str(definitive_catalog)
        report_snapshot = str(validation_report)

        engine.audit(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_report,
            ),
        )

        assert str(definitive_catalog) == catalog_snapshot
        assert str(validation_report) == report_snapshot

    def test_report_prepared_for_module_certification(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
        )

        result = engine.audit(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_report,
            ),
        )

        assert result.report.module_certification_prepared is True
        assert result.report.report_id.startswith("pm6-cqf-report://")

    def test_detects_duplicate_identifiers(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        duplicate_catalog = copy.deepcopy(definitive_catalog)
        models = list(duplicate_catalog.get("models", []))
        if len(models) < 1:
            pytest.skip("Se requiere al menos un modelo para probar unicidad")

        duplicate = copy.deepcopy(models[0])
        duplicate_catalog["models"] = models + [duplicate]

        result = engine.audit(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=duplicate_catalog,
                validation_report=validation_report,
            ),
        )

        assert any(
            finding.category.value == "uniqueness" and finding.severity == "error"
            for finding in result.report.findings
        )

    def test_rejects_invalid_inputs(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()

        with pytest.raises(ComparativeQualityInputAccessError):
            engine.audit(
                ComparativeQualityValidationRequest(
                    process_id=uuid4(),
                    definitive_catalog={"catalog_id": "invalid"},
                    validation_report={"report_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ComparativeQualityFrameworkCore(config_provider=config)
        engine.initialize()

        settings = config.comparative_tables().comparative_quality_framework
        assert settings.enabled is True
        assert settings.architectural_compliance_validator_enabled is True
        assert settings.module_certification_prepared is True

    def test_governance_declares_acceptance_criteria(self):
        assert "clean_architecture_compliance" in CQF_ACCEPTANCE_CRITERIA
        assert "pipeline_continuity" in CQF_ACCEPTANCE_CRITERIA
        assert "module_certification_prepared" in CQF_ACCEPTANCE_CRITERIA

    def test_gateway_does_not_access_source_documents(self):
        engine = ComparativeQualityFrameworkCore()
        engine.initialize()

        snapshot = engine.snapshot()
        assert snapshot["gateway"]["accesses_source_files"] is False
        assert snapshot["gateway"]["modifies_definitive_catalog"] is False
        assert snapshot["gateway"]["modifies_validation_report"] is False

    def test_package_does_not_import_forbidden_pm6_chains(self):
        package = importlib.import_module(
            "zovrake_motor.comparative_tables.comparative_quality_framework",
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


class TestComparativeQualityIntegration:
    def test_service_executes_through_pipeline(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
        )

        result = service.audit_comparative_quality(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_report,
                pipeline_snapshot=service.get_comparative_tables_pipeline_snapshot(),
            ),
        )

        assert service.comparative_quality_framework is not None
        assert service.comparative_quality_framework.report_store.count() == 1
        assert result.validators_executed == 6

    def test_pipeline_registers_quality_as_final_functional_stage(self):
        service = ComparativeTablesService()
        service.initialize()
        snapshot = ComparativeTablesPipeline.build_snapshot(service.component_registry)
        cqf_stage = next(
            item
            for item in snapshot
            if item["phase"] == ComparativeTablesPhase.VALIDACION_CALIDAD.value
        )
        assert cqf_stage["component_name"] == "comparative_quality_framework"
        assert cqf_stage["component_registered"] is True
        assert cqf_stage["component_ready"] is True
        assert (
            ComparativeTablesPipeline.comparative_quality_phase()
            == ComparativeTablesPhase.VALIDACION_CALIDAD
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
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        service.audit_comparative_quality(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_report,
            ),
        )

        process_state = state_manager.get_process(process_id)
        assert process_state is not None
        assert process_state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_validates_pipeline_flow_with_snapshot(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
        )

        result = service.audit_comparative_quality(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
                validation_report=validation_report,
                pipeline_snapshot=service.get_comparative_tables_pipeline_snapshot(),
            ),
        )

        pipeline_checks = [
            check for check in result.report.checks if check.category.value == "pipeline"
        ]
        assert pipeline_checks
        assert any(
            check.check_name == "validation_stage_ready" for check in pipeline_checks
        )

    def test_cmb_to_cqf_flow_preserves_lineage(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, validation_report, _ = build_quality_audit_inputs(
            process_id=process_id,
        )
        catalog_id = definitive_catalog["catalog_id"]

        result = service.audit_comparative_quality(
            ComparativeQualityValidationRequest(
                process_id=process_id,
                definitive_catalog=copy.deepcopy(definitive_catalog),
                validation_report=copy.deepcopy(validation_report),
            ),
        )

        assert result.report.catalog_id == catalog_id
        assert result.status in (
            ComparativeQualityValidationStatus.PASSED,
            ComparativeQualityValidationStatus.PASSED_WITH_WARNINGS,
            ComparativeQualityValidationStatus.SKIPPED,
        )

    def test_module_ready_count_includes_cqf(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10
