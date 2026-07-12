"""Pruebas del Comparable Group Builder — Implementación 3.7."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.comparable_group_builder import (
    ComparableGroupBuilderEngine,
    ComparableGroupBuildRequest,
    EquivalenceCatalogAccessError,
)
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.equivalence_detection import (
    EquivalenceDetectionEngine,
    EquivalenceDetectionRequest,
)
from zovrake_motor.classification.equivalence_detection.enums import EquivalenceRelationType
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_equivalence_detection import build_normalized_catalog_with_duplicate


def build_equivalence_catalog(*, process_id=None, document_id: str = "DOC-001") -> dict:
    process_id = process_id or uuid4()
    normalized_catalog = build_normalized_catalog_with_duplicate(process_id=process_id)
    ede = EquivalenceDetectionEngine()
    ede.initialize()
    return ede.detect(
        EquivalenceDetectionRequest(
            process_id=process_id,
            normalized_catalog=normalized_catalog,
        ),
    ).catalog.to_dict()


class TestComparableGroupBuilderEngine:
    def test_engine_initializes_with_one_builder(self):
        engine = ComparableGroupBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_comparable_groups_from_equivalences(self):
        engine = ComparableGroupBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)

        result = engine.build(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        equivalent = [
            record
            for record in catalog_dict["equivalences"]
            if record["relation_type"] == EquivalenceRelationType.EQUIVALENT.value
        ]
        if equivalent:
            assert len(result.catalog.groups) >= 1
            group = result.catalog.groups[0]
            assert group.group_id.startswith("GC-")
            assert group.internal_group_id.startswith("cgb://")
            assert len(group.normalized_concept_ids) >= 2

    def test_assigns_unique_immutable_group_ids(self):
        engine = ComparableGroupBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)

        result = engine.build(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        group_ids = [group.group_id for group in result.catalog.groups]
        assert len(group_ids) == len(set(group_ids))
        for group_id in group_ids:
            assert group_id.startswith("GC-")
            parts = group_id.split("-", 1)
            assert len(parts) == 2
            assert parts[1].isdigit()
            assert len(parts[1]) == 6

    def test_preserves_equivalence_catalog_and_traceability(self):
        engine = ComparableGroupBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)
        original_snapshot = str(catalog_dict)

        result = engine.build(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot
        assert result.equivalence_catalog_preserved is True
        if result.catalog.groups:
            group = result.catalog.groups[0]
            payload = group.to_dict()
            assert payload["traceability"]["source_equivalence_catalog_id"]
            assert payload["traceability"]["source_normalized_catalog_id"]
            assert payload["traceability"]["equivalence_ids"]
            assert payload["traceability"]["original_preserved"] is True

    def test_catalog_prepared_for_downstream_engines(self):
        engine = ComparableGroupBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)

        result = engine.build(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        catalog = result.catalog
        assert catalog.context_association_prepared is True
        assert catalog.comparative_domain_model_prepared is True

    def test_rejects_invalid_equivalence_catalog(self):
        engine = ComparableGroupBuilderEngine()
        engine.initialize()

        with pytest.raises(EquivalenceCatalogAccessError):
            engine.build(
                ComparableGroupBuildRequest(
                    process_id=uuid4(),
                    equivalence_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ComparableGroupBuilderEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().comparable_group_builder
        assert settings.enabled is True
        assert settings.equivalence_cluster_builder_enabled is True
        assert settings.group_id_prefix == "GC"
        assert settings.group_id_immutable is True


class TestComparableGroupBuilderIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)

        result = service.build_comparable_groups(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        assert service.comparable_group_builder is not None
        assert service.comparable_group_builder.catalog_store.count() == 1
        assert result.builders_executed == 1

    def test_pipeline_registers_comparable_group_build_as_seventh_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        group_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.CONSTRUCCION_GRUPOS.value
        )
        assert group_stage["component_name"] == "comparable_group_builder"
        assert group_stage["component_registered"] is True
        assert group_stage["component_ready"] is True
        assert (
            ClassificationPipeline.comparable_group_build_phase()
            == ClassificationPhase.CONSTRUCCION_GRUPOS
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
        catalog_dict = build_equivalence_catalog(process_id=process_id)

        service.build_comparable_groups(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cgb(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_groups_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = ComparableGroupBuilderSettings(max_groups_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                comparable_group_builder=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = ComparableGroupBuilderEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)

        result = engine.build(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.groups) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_ede_to_cgb_flow_preserves_lineage(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_equivalence_catalog(process_id=process_id)
        equivalence_catalog_id = catalog_dict["catalog_id"]

        result = service.build_comparable_groups(
            ComparableGroupBuildRequest(
                process_id=process_id,
                equivalence_catalog=copy.deepcopy(catalog_dict),
            ),
        )

        assert result.catalog.source_equivalence_catalog_id == equivalence_catalog_id
        if result.catalog.groups:
            group = result.catalog.groups[0]
            assert group.traceability.source_equivalence_catalog_id == equivalence_catalog_id
            assert group.traceability.model_id == catalog_dict["model_id"]
