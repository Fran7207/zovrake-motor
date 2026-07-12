"""Pruebas del Concept Normalization Engine — Implementación 3.5."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.concept_analysis import ConceptAnalysisEngine, ConceptAnalysisRequest
from zovrake_motor.classification.concept_normalization import (
    ClassificationCatalogAccessError,
    ConceptNormalizationEngine,
    ConceptNormalizationRequest,
)
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.material_classification import MaterialClassificationRequest
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.classification.service_classification import ServiceClassificationRequest
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ConceptNormalizationSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_concept_analysis import build_internal_model_dict


def build_classification_catalogs(*, process_id=None, document_id: str = "DOC-001") -> tuple[dict, dict]:
    process_id = process_id or uuid4()
    cae = ConceptAnalysisEngine()
    cae.initialize()
    model_dict = build_internal_model_dict(process_id=process_id, document_id=document_id)
    catalog_dict = cae.analyze(
        ConceptAnalysisRequest(
            process_id=process_id,
            internal_model=model_dict,
        ),
    ).catalog.to_dict()

    from zovrake_motor.classification.material_classification import MaterialClassificationEngine
    from zovrake_motor.classification.service_classification import ServiceClassificationEngine

    mce = MaterialClassificationEngine()
    mce.initialize()
    material_catalog = mce.classify(
        MaterialClassificationRequest(
            process_id=process_id,
            concept_catalog=catalog_dict,
        ),
    ).catalog.to_dict()

    sce = ServiceClassificationEngine()
    sce.initialize()
    service_catalog = sce.classify(
        ServiceClassificationRequest(
            process_id=process_id,
            concept_catalog=catalog_dict,
        ),
    ).catalog.to_dict()

    return material_catalog, service_catalog


class TestConceptNormalizationEngine:
    def test_engine_initializes_with_six_normalizers(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 6

    def test_normalizes_materials_and_services(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        result = engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        assert len(result.catalog.concepts) >= 1
        concept_types = {concept.concept_type for concept in result.catalog.concepts}
        assert concept_types  # al menos un tipo representado

    def test_preserves_original_value(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        result = engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        for concept in result.catalog.concepts:
            assert concept.original_value
            assert concept.normalized_value is not None
            assert concept.original_value != concept.normalized_value or concept.original_value == concept.normalized_value.lower()

    def test_preserves_traceability_and_uniform_structure(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        result = engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        for concept in result.catalog.concepts:
            payload = concept.to_dict()
            assert payload["normalized_concept_id"].startswith("cne://")
            assert payload["concept_id"].startswith("cae://")
            assert payload["original_value"]
            assert payload["normalized_value"]
            assert payload["traceability"]["canonical_reference"]
            assert payload["traceability"]["source_reference"]
            assert payload["model_reference"]["source_record_id"]
            assert payload["model_reference"]["model_id"]

    def test_does_not_modify_source_catalogs(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)
        material_snapshot = str(material_catalog)
        service_snapshot = str(service_catalog)

        engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        assert str(material_catalog) == material_snapshot
        assert str(service_catalog) == service_snapshot
        assert engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        ).source_catalogs_preserved is True

    def test_catalog_prepared_for_downstream_engines(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        result = engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        catalog = result.catalog
        assert catalog.equivalence_detection_prepared is True
        assert catalog.comparable_group_builder_prepared is True

    def test_rejects_invalid_catalogs(self):
        engine = ConceptNormalizationEngine()
        engine.initialize()

        with pytest.raises(ClassificationCatalogAccessError):
            engine.normalize(
                ConceptNormalizationRequest(
                    process_id=uuid4(),
                    material_catalog={"catalog_id": "invalid"},
                    service_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ConceptNormalizationEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().concept_normalization
        assert settings.enabled is True
        assert settings.material_normalizer_enabled is True
        assert settings.specification_normalizer_enabled is True


class TestConceptNormalizationIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        result = service.normalize_concepts(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        assert len(result.catalog.concepts) >= 1
        assert service.concept_normalization_engine is not None
        assert service.concept_normalization_engine.catalog_store.count() == 1

    def test_pipeline_registers_normalization_as_fourth_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        normalization_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.NORMALIZACION_CONCEPTOS.value
        )
        assert normalization_stage["component_name"] == "concept_normalization_engine"
        assert normalization_stage["component_registered"] is True
        assert normalization_stage["component_ready"] is True
        assert (
            ClassificationPipeline.concept_normalization_phase()
            == ClassificationPhase.NORMALIZACION_CONCEPTOS
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
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        service.normalize_concepts(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cne(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_concepts_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = ConceptNormalizationSettings(max_normalized_concepts_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                concept_normalization=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = ConceptNormalizationEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        material_catalog, service_catalog = build_classification_catalogs(process_id=process_id)

        result = engine.normalize(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=material_catalog,
                service_catalog=service_catalog,
            ),
        )

        assert len(result.catalog.concepts) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_mce_sce_to_cne_flow_preserves_lineage(self):
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
        cne_result = service.normalize_concepts(
            ConceptNormalizationRequest(
                process_id=process_id,
                material_catalog=mce_result.catalog.to_dict(),
                service_catalog=sce_result.catalog.to_dict(),
            ),
        )

        assert cne_result.catalog.source_material_catalog_id == mce_result.catalog.catalog_id
        assert cne_result.catalog.source_service_catalog_id == sce_result.catalog.catalog_id
        if cne_result.catalog.concepts:
            concept = cne_result.catalog.concepts[0]
            assert concept.traceability.model_id == cae_result.model_id
