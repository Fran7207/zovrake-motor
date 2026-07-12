"""Pruebas del Equivalence Detection Engine — Implementación 3.6."""

from __future__ import annotations

import copy
from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.concept_analysis import ConceptAnalysisRequest
from zovrake_motor.classification.concept_normalization import ConceptNormalizationRequest
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.equivalence_detection import (
    EquivalenceDetectionEngine,
    EquivalenceDetectionRequest,
    NormalizedCatalogAccessError,
)
from zovrake_motor.classification.equivalence_detection.enums import EquivalenceRelationType
from zovrake_motor.classification.material_classification import MaterialClassificationRequest
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.classification.service_classification import ServiceClassificationRequest
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import EquivalenceDetectionSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_concept_analysis import build_internal_model_dict
from tests.unit.test_concept_normalization import build_classification_catalogs


def build_normalized_catalog(*, process_id=None, document_id: str = "DOC-001") -> dict:
    from zovrake_motor.classification.concept_normalization import ConceptNormalizationEngine

    process_id = process_id or uuid4()
    material_catalog, service_catalog = build_classification_catalogs(
        process_id=process_id,
        document_id=document_id,
    )
    cne = ConceptNormalizationEngine()
    cne.initialize()
    return cne.normalize(
        ConceptNormalizationRequest(
            process_id=process_id,
            material_catalog=material_catalog,
            service_catalog=service_catalog,
        ),
    ).catalog.to_dict()


def build_normalized_catalog_with_duplicate(*, process_id=None) -> dict:
    catalog = build_normalized_catalog(process_id=process_id)
    concepts = list(catalog["concepts"])
    if not concepts:
        pytest.skip("No hay conceptos normalizados para probar equivalencias")

    duplicate = copy.deepcopy(concepts[0])
    duplicate["normalized_concept_id"] = duplicate["normalized_concept_id"].replace(
        "concept-",
        "concept-dup-",
    )
    concepts.append(duplicate)
    catalog["concepts"] = concepts
    return catalog


class TestEquivalenceDetectionEngine:
    def test_engine_initializes_with_three_detectors(self):
        engine = EquivalenceDetectionEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 3

    def test_detects_equivalence_relations(self):
        engine = EquivalenceDetectionEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_normalized_catalog_with_duplicate(process_id=process_id)

        result = engine.detect(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        equivalent = [
            record
            for record in result.catalog.equivalences
            if record.relation_type == EquivalenceRelationType.EQUIVALENT.value
        ]
        assert len(equivalent) >= 1

    def test_detects_distinct_relations_for_cross_type_matches(self):
        engine = EquivalenceDetectionEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_normalized_catalog(process_id=process_id)
        concepts = list(catalog_dict["concepts"])
        if len(concepts) < 2:
            pytest.skip("Se requieren al menos dos conceptos para probar diferenciación")

        left = copy.deepcopy(concepts[0])
        right = copy.deepcopy(concepts[1])
        right["normalized_value"] = left["normalized_value"]
        right["concept_type"] = "distinct_test_type"
        right["normalized_concept_id"] = "cne://test/distinct-0001"
        catalog_dict["concepts"] = concepts + [right]

        result = engine.detect(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        distinct = [
            record
            for record in result.catalog.equivalences
            if record.relation_type == EquivalenceRelationType.DISTINCT.value
        ]
        assert len(distinct) >= 1

    def test_preserves_original_catalog_and_explainability(self):
        engine = EquivalenceDetectionEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_normalized_catalog_with_duplicate(process_id=process_id)
        original_snapshot = str(catalog_dict)

        result = engine.detect(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        assert str(catalog_dict) == original_snapshot
        assert result.normalized_catalog_preserved is True
        if result.catalog.equivalences:
            record = result.catalog.equivalences[0]
            payload = record.to_dict()
            assert payload["equivalence_id"].startswith("ede://")
            assert payload["explainability"]["criteria_used"]
            assert payload["explainability"]["information_used"]
            assert payload["explainability"]["limitations"]
            assert payload["traceability"]["source_normalized_catalog_id"]

    def test_catalog_prepared_for_downstream_engines(self):
        engine = EquivalenceDetectionEngine()
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_normalized_catalog(process_id=process_id)

        result = engine.detect(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        catalog = result.catalog
        assert catalog.comparable_group_builder_prepared is True
        assert catalog.context_association_prepared is True
        assert catalog.comparative_domain_model_prepared is True

    def test_rejects_invalid_normalized_catalog(self):
        engine = EquivalenceDetectionEngine()
        engine.initialize()

        with pytest.raises(NormalizedCatalogAccessError):
            engine.detect(
                EquivalenceDetectionRequest(
                    process_id=uuid4(),
                    normalized_catalog={"catalog_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = EquivalenceDetectionEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().equivalence_detection
        assert settings.enabled is True
        assert settings.exact_match_detector_enabled is True
        assert settings.cross_type_distinct_detector_enabled is True
        assert settings.shared_origin_relation_detector_enabled is True


class TestEquivalenceDetectionIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        catalog_dict = build_normalized_catalog_with_duplicate(process_id=process_id)

        result = service.detect_equivalences(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        assert service.equivalence_detection_engine is not None
        assert service.equivalence_detection_engine.catalog_store.count() == 1
        assert result.detectors_executed == 3

    def test_pipeline_registers_equivalence_detection_as_fifth_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        equivalence_stage = next(
            item
            for item in snapshot
            if item["phase"] == ClassificationPhase.DETECCION_EQUIVALENCIAS.value
        )
        assert equivalence_stage["component_name"] == "equivalence_detection_engine"
        assert equivalence_stage["component_registered"] is True
        assert equivalence_stage["component_ready"] is True
        assert (
            ClassificationPipeline.equivalence_detection_phase()
            == ClassificationPhase.DETECCION_EQUIVALENCIAS
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
        catalog_dict = build_normalized_catalog_with_duplicate(process_id=process_id)

        service.detect_equivalences(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_ede(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_respects_max_equivalences_configuration(self):
        from dataclasses import replace

        config = ConfigurationProvider.default()
        limited = EquivalenceDetectionSettings(max_equivalences_per_process=0)
        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                equivalence_detection=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = EquivalenceDetectionEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        catalog_dict = build_normalized_catalog_with_duplicate(process_id=process_id)

        result = engine.detect(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=catalog_dict,
            ),
        )

        assert len(result.catalog.equivalences) == 0
        assert any(incident.severity == "warning" for incident in result.incidents)

    def test_cne_to_ede_flow_preserves_lineage(self):
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
        normalized_dict = copy.deepcopy(cne_result.catalog.to_dict())
        if normalized_dict["concepts"]:
            duplicate = copy.deepcopy(normalized_dict["concepts"][0])
            duplicate["normalized_concept_id"] = duplicate["normalized_concept_id"].replace(
                "concept-",
                "concept-dup-",
            )
            normalized_dict["concepts"].append(duplicate)

        ede_result = service.detect_equivalences(
            EquivalenceDetectionRequest(
                process_id=process_id,
                normalized_catalog=normalized_dict,
            ),
        )

        assert ede_result.catalog.source_normalized_catalog_id == cne_result.catalog.catalog_id
        if ede_result.catalog.equivalences:
            equivalence = ede_result.catalog.equivalences[0]
            assert equivalence.traceability.model_id == cne_result.model_id
