"""Pruebas del Material Classification Engine — Implementación 3.3."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.concept_analysis import ConceptAnalysisEngine, ConceptAnalysisRequest, ConceptKind
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.material_classification import (
    ConceptCatalogAccessError,
    MaterialClassificationEngine,
    MaterialClassificationRequest,
)
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import MaterialClassificationSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_concept_analysis import build_internal_model_dict


def build_cae_catalog(*, process_id=None, document_id: str = "DOC-001") -> dict:
    process_id = process_id or uuid4()
    cae = ConceptAnalysisEngine()
    cae.initialize()
    model_dict = build_internal_model_dict(process_id=process_id, document_id=document_id)
    result = cae.analyze(
        ConceptAnalysisRequest(
            process_id=process_id,
            internal_model=model_dict,
        ),
    )
    return result.catalog.to_dict()


class TestMaterialClassificationEngine:
    def test_engine_initializes_with_two_classifiers(self):
        engine = MaterialClassificationEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 2

    def test_classifies_only_material_concepts(self):
        engine = MaterialClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.materials) >= 1
        assert all(
            material.concept_kind in {ConceptKind.ITEM.value, ConceptKind.PARTIDA.value}
            for material in result.catalog.materials
        )

    def test_does_not_classify_non_material_concepts(self):
        engine = MaterialClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)
        concept_kinds = {concept["kind"] for concept in catalog_dict["concepts"]}
        non_material = concept_kinds - {ConceptKind.ITEM.value, ConceptKind.PARTIDA.value}

        result = engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        classified_concept_ids = {material.concept_id for material in result.catalog.materials}
        for concept in catalog_dict["concepts"]:
            if concept["kind"] in non_material:
                assert concept["concept_id"] not in classified_concept_ids

    def test_preserves_traceability_and_uniform_structure(self):
        engine = MaterialClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        for material in result.catalog.materials:
            payload = material.to_dict()
            assert payload["material_id"].startswith("mce://")
            assert payload["concept_id"].startswith("cae://")
            assert payload["original_name"]
            assert payload["traceability"]["canonical_reference"]
            assert payload["traceability"]["source_reference"]
            assert payload["model_reference"]["model_id"]
            assert payload["model_reference"]["concept_id"] == payload["concept_id"]

    def test_does_not_modify_concept_catalog(self):
        engine = MaterialClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)
        original_snapshot = str(catalog_dict)

        engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot
        assert engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        ).concept_catalog_preserved is True

    def test_catalog_prepared_for_downstream_engines(self):
        engine = MaterialClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        catalog = result.catalog
        assert catalog.service_classification_prepared is True
        assert catalog.normalization_prepared is True
        assert catalog.equivalence_detection_prepared is True
        assert catalog.comparable_group_builder_prepared is True

    def test_rejects_invalid_concept_catalog(self):
        engine = MaterialClassificationEngine()
        engine.initialize()

        with pytest.raises(ConceptCatalogAccessError):
            engine.classify(
                MaterialClassificationRequest(
                    process_id=uuid4(),
                    concept_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = MaterialClassificationEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().material_classification
        assert settings.enabled is True
        assert settings.item_classifier_enabled is True
        assert settings.partida_classifier_enabled is True


class TestMaterialClassificationIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = service.classify_materials(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.materials) >= 1
        assert service.material_classification_engine is not None
        assert service.material_classification_engine.catalog_store.count() == 1

    def test_pipeline_registers_material_classification_as_second_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        material_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.CLASIFICACION_MATERIALES.value
        )
        assert material_stage["component_name"] == "material_classification_engine"
        assert material_stage["component_registered"] is True
        assert material_stage["component_ready"] is True
        assert (
            ClassificationPipeline.material_classification_phase()
            == ClassificationPhase.CLASIFICACION_MATERIALES
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
        catalog_dict = build_cae_catalog(process_id=process_id)

        service.classify_materials(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_mce(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_materials_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = MaterialClassificationSettings(max_materials_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                material_classification=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = MaterialClassificationEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.materials) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_cae_to_mce_flow_preserves_lineage(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        cae_result = service.analyze_concepts(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )
        mce_result = service.classify_materials(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=cae_result.catalog.to_dict(),
            ),
        )

        assert mce_result.catalog.source_concept_catalog_id == cae_result.catalog.catalog_id
        if mce_result.catalog.materials:
            material = mce_result.catalog.materials[0]
            assert material.traceability.model_id == cae_result.model_id
            assert material.concept_id in {c.concept_id for c in cae_result.catalog.concepts}
