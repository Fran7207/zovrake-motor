"""Pruebas del Comparative Domain Model Builder — Implementación 3.9."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.comparative_domain_model import (
    ComparativeDomainModelBuilderEngine,
    ComparativeDomainModelBuildRequest,
    ContextAssociationCatalogAccessError,
)
from zovrake_motor.classification.context_association import (
    ContextAssociationEngine,
    ContextAssociationRequest,
)
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_context_association import (
    build_comparable_group_catalog,
    build_integrated_context,
)


def build_context_association_catalog(*, process_id=None) -> dict:
    process_id = process_id or uuid4()
    group_catalog = build_comparable_group_catalog(process_id=process_id)
    context = build_integrated_context(process_id=process_id)
    cae = ContextAssociationEngine()
    cae.initialize()
    return cae.associate(
        ContextAssociationRequest(
            process_id=process_id,
            comparable_group_catalog=group_catalog,
            integrated_context=context,
        ),
    ).catalog.to_dict()


class TestComparativeDomainModelBuilderEngine:
    def test_engine_initializes_with_one_builder(self):
        engine = ComparativeDomainModelBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_comparative_domain_models(self):
        engine = ComparativeDomainModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)

        result = engine.build(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        associations_count = len(catalog_dict.get("associations", []))
        if associations_count:
            assert len(result.catalog.models) == associations_count
            model = result.catalog.models[0]
            assert model.comparative_model_id.startswith("CDM-")
            assert model.related_context.description
            assert model.traceability.context_preserved is True

    def test_assigns_unique_model_ids(self):
        engine = ComparativeDomainModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)

        result = engine.build(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        model_ids = [model.comparative_model_id for model in result.catalog.models]
        assert len(model_ids) == len(set(model_ids))
        for model_id in model_ids:
            assert model_id.startswith("CDM-")

    def test_preserves_source_data_and_traceability(self):
        engine = ComparativeDomainModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)
        original_snapshot = str(catalog_dict)

        result = engine.build(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot
        assert result.source_data_preserved is True
        if result.catalog.models:
            model = result.catalog.models[0]
            payload = model.to_dict()
            assert payload["traceability"]["source_context_association_catalog_id"]
            assert payload["traceability"]["source_comparable_group_catalog_id"]
            assert payload["related_context"]["description"]

    def test_catalog_is_pm6_output_contract(self):
        engine = ComparativeDomainModelBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)

        result = engine.build(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        assert result.catalog.pm6_output_contract is True
        assert result.catalog.source_data_preserved is True

    def test_rejects_invalid_association_catalog(self):
        engine = ComparativeDomainModelBuilderEngine()
        engine.initialize()

        with pytest.raises(ContextAssociationCatalogAccessError):
            engine.build(
                ComparativeDomainModelBuildRequest(
                    process_id=uuid4(),
                    context_association_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ComparativeDomainModelBuilderEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().comparative_domain_model_builder
        assert settings.enabled is True
        assert settings.group_context_aggregation_builder_enabled is True
        assert settings.pm6_output_contract is True
        assert settings.model_id_prefix == "CDM"


class TestComparativeDomainModelBuilderIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)

        result = service.build_comparative_domain_model(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        assert service.comparative_domain_model_builder is not None
        assert service.comparative_domain_model_builder.catalog_store.count() == 1
        assert result.builders_executed == 1

    def test_pipeline_registers_domain_model_as_last_pm5_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        domain_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.MODELO_DOMINIO.value
        )
        assert domain_stage["component_name"] == "comparative_domain_model_builder"
        assert domain_stage["component_registered"] is True
        assert domain_stage["component_ready"] is True
        assert (
            ClassificationPipeline.comparative_domain_model_phase()
            == ClassificationPhase.MODELO_DOMINIO
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
        catalog_dict = build_context_association_catalog(process_id=process_id)

        service.build_comparative_domain_model(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cdmb(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_models_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = ComparativeDomainModelBuilderSettings(max_models_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                comparative_domain_model_builder=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = ComparativeDomainModelBuilderEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)

        result = engine.build(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.models) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_cae_to_cdmb_flow_preserves_lineage(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_context_association_catalog(process_id=process_id)
        association_catalog_id = catalog_dict["catalog_id"]

        result = service.build_comparative_domain_model(
            ComparativeDomainModelBuildRequest(
                process_id=process_id,
                context_association_catalog=copy.deepcopy(catalog_dict),
            ),
        )

        assert result.catalog.source_context_association_catalog_id == association_catalog_id
        if result.catalog.models:
            model = result.catalog.models[0]
            assert model.traceability.source_context_association_catalog_id == association_catalog_id
            assert model.related_context.description == catalog_dict["preserved_context"]["description"]
