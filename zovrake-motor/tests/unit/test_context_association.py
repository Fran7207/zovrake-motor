"""Pruebas del Context Association Engine — Implementación 3.8."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.context_association import (
    ComparableGroupCatalogAccessError,
    ContextAssociationEngine,
    ContextAssociationRequest,
    IntegratedContextAccessError,
)
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ContextAssociationSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparable_group_builder import build_equivalence_catalog
from zovrake_motor.classification.comparable_group_builder import (
    ComparableGroupBuilderEngine,
    ComparableGroupBuildRequest,
)


def build_comparable_group_catalog(*, process_id=None) -> dict:
    process_id = process_id or uuid4()
    equivalence_catalog = build_equivalence_catalog(process_id=process_id)
    cgb = ComparableGroupBuilderEngine()
    cgb.initialize()
    return cgb.build(
        ComparableGroupBuildRequest(
            process_id=process_id,
            equivalence_catalog=equivalence_catalog,
        ),
    ).catalog.to_dict()


def build_integrated_context(*, process_id=None, description: str = "Detalles del requerimiento de prueba") -> dict:
    process_id = process_id or uuid4()
    return {
        "context_id": f"ctx://{process_id}",
        "description": description,
        "process_id": str(process_id),
        "codigo_req": "REQ-TEST",
        "immutable": True,
    }


class TestContextAssociationEngine:
    def test_engine_initializes_with_one_associator(self):
        engine = ContextAssociationEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_associates_context_with_each_group(self):
        engine = ContextAssociationEngine()
        engine.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)

        result = engine.associate(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_catalog,
                integrated_context=context,
            ),
        )

        groups_count = len(group_catalog.get("groups", []))
        if groups_count:
            assert len(result.catalog.associations) == groups_count
            assert result.catalog.associations[0].context_id == context["context_id"]

    def test_preserves_context_and_groups(self):
        engine = ContextAssociationEngine()
        engine.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)
        original_groups = str(group_catalog)
        original_context = str(context)

        result = engine.associate(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_catalog,
                integrated_context=context,
            ),
        )

        assert str(group_catalog) == original_groups
        assert str(context) == original_context
        assert result.comparable_group_catalog_preserved is True
        assert result.context_preserved is True
        assert result.catalog.preserved_context.description == context["description"]

    def test_catalog_prepared_for_domain_model_builder(self):
        engine = ContextAssociationEngine()
        engine.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)

        result = engine.associate(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_catalog,
                integrated_context=context,
            ),
        )

        assert result.catalog.comparative_domain_model_prepared is True

    def test_rejects_invalid_group_catalog(self):
        engine = ContextAssociationEngine()
        engine.initialize()

        with pytest.raises(ComparableGroupCatalogAccessError):
            engine.associate(
                ContextAssociationRequest(
                    process_id=uuid4(),
                    comparable_group_catalog={"catalog_id": "invalid"},
                    integrated_context=build_integrated_context(),
                ),
            )

    def test_rejects_invalid_context(self):
        engine = ContextAssociationEngine()
        engine.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)

        with pytest.raises(IntegratedContextAccessError):
            engine.associate(
                ContextAssociationRequest(
                    process_id=process_id,
                    comparable_group_catalog=group_catalog,
                    integrated_context={"context_id": "ctx-invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ContextAssociationEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().context_association
        assert settings.enabled is True
        assert settings.uniform_group_context_associator_enabled is True
        assert settings.preserve_context_immutability is True


class TestContextAssociationIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)

        result = service.associate_context(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_catalog,
                integrated_context=context,
            ),
        )

        assert service.context_association_engine is not None
        assert service.context_association_engine.catalog_store.count() == 1
        assert result.associators_executed == 1

    def test_pipeline_registers_context_association_as_ninth_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        context_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.ASOCIACION_CONTEXTO.value
        )
        assert context_stage["component_name"] == "context_association_engine"
        assert context_stage["component_registered"] is True
        assert context_stage["component_ready"] is True
        assert (
            ClassificationPipeline.context_association_phase()
            == ClassificationPhase.ASOCIACION_CONTEXTO
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
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)

        service.associate_context(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_catalog,
                integrated_context=context,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_respects_max_associations_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = ContextAssociationSettings(max_associations_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                context_association=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = ContextAssociationEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)

        result = engine.associate(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=group_catalog,
                integrated_context=context,
            ),
        )

        assert len(result.catalog.associations) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_cgb_to_cae_flow_preserves_lineage(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        group_catalog = build_comparable_group_catalog(process_id=process_id)
        context = build_integrated_context(process_id=process_id)

        result = service.associate_context(
            ContextAssociationRequest(
                process_id=process_id,
                comparable_group_catalog=copy.deepcopy(group_catalog),
                integrated_context=copy.deepcopy(context),
            ),
        )

        assert result.catalog.source_comparable_group_catalog_id == group_catalog["catalog_id"]
        if result.catalog.associations:
            association = result.catalog.associations[0]
            assert association.traceability.source_comparable_group_catalog_id == group_catalog["catalog_id"]
