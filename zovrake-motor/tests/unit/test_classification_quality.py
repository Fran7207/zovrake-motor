"""Pruebas del Classification Quality Framework — Implementación 3.10."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.classification_quality import (
    ClassificationQualityFrameworkEngine,
    ClassificationQualityValidationRequest,
    ComparativeDomainModelCatalogAccessError,
    QualityValidationStatus,
)
from zovrake_motor.classification.comparative_domain_model import (
    ComparativeDomainModelBuilderEngine,
    ComparativeDomainModelBuildRequest,
)
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ClassificationQualityFrameworkSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_domain_model import build_context_association_catalog


def build_comparative_domain_model_catalog(*, process_id=None) -> dict:
    process_id = process_id or uuid4()
    association_catalog = build_context_association_catalog(process_id=process_id)
    cdmb = ComparativeDomainModelBuilderEngine()
    cdmb.initialize()
    return cdmb.build(
        ComparativeDomainModelBuildRequest(
            process_id=process_id,
            context_association_catalog=association_catalog,
        ),
    ).catalog.to_dict()


class TestClassificationQualityFrameworkEngine:
    def test_engine_initializes_with_five_validators(self):
        engine = ClassificationQualityFrameworkEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 5

    def test_validates_comparative_domain_model(self):
        engine = ClassificationQualityFrameworkEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)

        result = engine.validate(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
            ),
        )

        assert result.report.checks_executed > 0
        assert result.source_data_preserved is True
        if catalog_dict.get("models"):
            assert result.report.checks_passed > 0

    def test_preserves_source_catalog(self):
        engine = ClassificationQualityFrameworkEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)
        original_snapshot = str(catalog_dict)

        engine.validate(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot

    def test_report_prepared_for_certification(self):
        engine = ClassificationQualityFrameworkEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)

        result = engine.validate(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
            ),
        )

        assert result.report.certification_prepared is True
        assert result.report.report_id.startswith("cqf-report://")

    def test_detects_duplicate_identifiers(self):
        engine = ClassificationQualityFrameworkEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)
        models = list(catalog_dict.get("models", []))
        if len(models) < 2:
            pytest.skip("Se requieren al menos dos modelos para probar unicidad")

        duplicate = copy.deepcopy(models[0])
        duplicate["comparative_model_id"] = models[1]["comparative_model_id"]
        catalog_dict["models"] = models + [duplicate]

        result = engine.validate(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
            ),
        )

        assert any(
            finding.category.value == "uniqueness" and finding.severity == "error"
            for finding in result.report.findings
        )

    def test_rejects_invalid_catalog(self):
        engine = ClassificationQualityFrameworkEngine()
        engine.initialize()

        with pytest.raises(ComparativeDomainModelCatalogAccessError):
            engine.validate(
                ClassificationQualityValidationRequest(
                    process_id=uuid4(),
                    comparative_domain_model_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ClassificationQualityFrameworkEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().classification_quality_framework
        assert settings.enabled is True
        assert settings.model_consistency_validator_enabled is True
        assert settings.certification_prepared is True


class TestClassificationQualityFrameworkIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)

        result = service.validate_classification_quality(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
                pipeline_snapshot=service.get_classification_pipeline_snapshot(),
            ),
        )

        assert service.classification_quality_framework is not None
        assert service.classification_quality_framework.report_store.count() == 1
        assert result.validators_executed == 5

    def test_pipeline_registers_quality_validation_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        quality_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.VALIDACION_CALIDAD.value
        )
        assert quality_stage["component_name"] == "classification_quality_framework"
        assert quality_stage["component_registered"] is True
        assert quality_stage["component_ready"] is True
        assert (
            ClassificationPipeline.quality_validation_phase()
            == ClassificationPhase.VALIDACION_CALIDAD
        )

    def test_records_state_and_events(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ClassificationService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)

        service.validate_classification_quality(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cqf(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_validates_pipeline_flow_with_snapshot(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)

        result = service.validate_classification_quality(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=catalog_dict,
                pipeline_snapshot=service.get_classification_pipeline_snapshot(),
            ),
        )

        pipeline_checks = [
            check for check in result.report.checks if check.category.value == "pipeline"
        ]
        assert pipeline_checks
        assert any(check.check_name == "domain_model_stage_ready" for check in pipeline_checks)

    def test_cdmb_to_cqf_flow_preserves_lineage(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_comparative_domain_model_catalog(process_id=process_id)
        catalog_id = catalog_dict["catalog_id"]

        result = service.validate_classification_quality(
            ClassificationQualityValidationRequest(
                process_id=process_id,
                comparative_domain_model_catalog=copy.deepcopy(catalog_dict),
            ),
        )

        assert result.report.catalog_id == catalog_id
        assert result.status in (
            QualityValidationStatus.PASSED,
            QualityValidationStatus.PASSED_WITH_WARNINGS,
            QualityValidationStatus.SKIPPED,
        )
