"""Pruebas del Service Classification Engine — Implementación 3.4."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.concept_analysis import ConceptAnalysisEngine, ConceptAnalysisRequest, ConceptKind
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.material_classification import MaterialClassificationRequest
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.classification.service_classification import (
    ConceptCatalogAccessError,
    ServiceClassificationEngine,
    ServiceClassificationRequest,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ServiceClassificationSettings
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


SERVICE_CONCEPT_KINDS = {
    ConceptKind.COMMERCIAL_CONDITION.value,
    ConceptKind.OBSERVATION.value,
    ConceptKind.TECHNICAL_ELEMENT.value,
}
MATERIAL_CONCEPT_KINDS = {ConceptKind.ITEM.value, ConceptKind.PARTIDA.value}


class TestServiceClassificationEngine:
    def test_engine_initializes_with_three_classifiers(self):
        engine = ServiceClassificationEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 3

    def test_classifies_only_service_concepts(self):
        engine = ServiceClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.services) >= 1
        assert all(
            service.concept_kind in SERVICE_CONCEPT_KINDS
            for service in result.catalog.services
        )

    def test_does_not_classify_material_concepts(self):
        engine = ServiceClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        classified_concept_ids = {service.concept_id for service in result.catalog.services}
        for concept in catalog_dict["concepts"]:
            if concept["kind"] in MATERIAL_CONCEPT_KINDS:
                assert concept["concept_id"] not in classified_concept_ids

    def test_preserves_traceability_and_uniform_structure(self):
        engine = ServiceClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        for service in result.catalog.services:
            payload = service.to_dict()
            assert payload["service_id"].startswith("sce://")
            assert payload["concept_id"].startswith("cae://")
            assert payload["original_name"]
            assert payload["traceability"]["canonical_reference"]
            assert payload["traceability"]["source_reference"]
            assert payload["model_reference"]["model_id"]
            assert payload["model_reference"]["concept_id"] == payload["concept_id"]

    def test_does_not_modify_concept_catalog(self):
        engine = ServiceClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)
        original_snapshot = str(catalog_dict)

        engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot
        assert engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        ).concept_catalog_preserved is True

    def test_catalog_prepared_for_downstream_engines(self):
        engine = ServiceClassificationEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        catalog = result.catalog
        assert catalog.normalization_prepared is True
        assert catalog.equivalence_detection_prepared is True
        assert catalog.comparable_group_builder_prepared is True

    def test_rejects_invalid_concept_catalog(self):
        engine = ServiceClassificationEngine()
        engine.initialize()

        with pytest.raises(ConceptCatalogAccessError):
            engine.classify(
                ServiceClassificationRequest(
                    process_id=uuid4(),
                    concept_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ServiceClassificationEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().service_classification
        assert settings.enabled is True
        assert settings.commercial_condition_classifier_enabled is True
        assert settings.observation_classifier_enabled is True
        assert settings.technical_element_classifier_enabled is True


class TestServiceClassificationIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = service.classify_services(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.services) >= 1
        assert service.service_classification_engine is not None
        assert service.service_classification_engine.catalog_store.count() == 1

    def test_pipeline_registers_service_classification_as_third_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        service_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.CLASIFICACION_SERVICIOS.value
        )
        assert service_stage["component_name"] == "service_classification_engine"
        assert service_stage["component_registered"] is True
        assert service_stage["component_ready"] is True
        assert (
            ClassificationPipeline.service_classification_phase()
            == ClassificationPhase.CLASIFICACION_SERVICIOS
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

        service.classify_services(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_sce(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_services_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = ServiceClassificationSettings(max_services_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                service_classification=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = ServiceClassificationEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_cae_catalog(process_id=process_id)

        result = engine.classify(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.services) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_cae_to_sce_flow_preserves_lineage(self):
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
        sce_result = service.classify_services(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=cae_result.catalog.to_dict(),
            ),
        )

        assert sce_result.catalog.source_concept_catalog_id == cae_result.catalog.catalog_id
        if sce_result.catalog.services:
            service_record = sce_result.catalog.services[0]
            assert service_record.traceability.model_id == cae_result.model_id
            assert service_record.concept_id in {c.concept_id for c in cae_result.catalog.concepts}

    def test_materials_and_services_remain_separated(self):
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
        catalog_dict = cae_result.catalog.to_dict()
        mce_result = service.classify_materials(
            MaterialClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )
        sce_result = service.classify_services(
            ServiceClassificationRequest(
                process_id=process_id,
                concept_catalog=catalog_dict,
            ),
        )

        material_concept_ids = {material.concept_id for material in mce_result.catalog.materials}
        service_concept_ids = {record.concept_id for record in sce_result.catalog.services}
        assert material_concept_ids.isdisjoint(service_concept_ids)
        assert mce_result.catalog.catalog_id != sce_result.catalog.catalog_id
