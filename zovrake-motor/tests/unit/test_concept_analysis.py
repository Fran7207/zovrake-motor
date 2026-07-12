"""Pruebas del Concept Analysis Engine — Implementación 3.2."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ClassificationService
from zovrake_motor.classification.concept_analysis import (
    ConceptAnalysisEngine,
    ConceptAnalysisRequest,
    ConceptKind,
    InternalModelAccessError,
)
from zovrake_motor.classification.enums import ClassificationPhase
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.comprehension.canonical import CanonicalRepresentationEngine, CanonicalRepresentationRequest
from zovrake_motor.comprehension.internal_model import InternalDocumentModelBuilder, InternalModelBuildRequest
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.classification import ConceptAnalysisSettings
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_document_internal_model import build_canonical_result, build_extraction_result


def build_internal_model_dict(*, process_id=None, document_id: str = "DOC-001") -> dict:
    process_id = process_id or uuid4()
    cre = CanonicalRepresentationEngine()
    cre.initialize()
    canonical = cre.represent(
        CanonicalRepresentationRequest(
            process_id=process_id,
            extraction_result=build_extraction_result(
                process_id=process_id,
                document_id=document_id,
                metadata={
                    "format_type": "pdf",
                    "document_reference": "adapter://pdf/DOC-001",
                    "provider_name": "Proveedor Test",
                    "commercial_currency": "USD",
                    "commercial_total": "1500.00",
                    "commercial_payment_terms": "30 días",
                    "technical_specifications": ("Acero inoxidable", "Resistencia 400 MPa"),
                    "commercial_conditions": (("Entrega", "15 días"),),
                    "observations": (("Nota", "Incluye instalación"),),
                },
            ),
        ),
    )
    idmb = InternalDocumentModelBuilder()
    idmb.initialize()
    result = idmb.build(
        InternalModelBuildRequest(
            process_id=process_id,
            canonical_result=canonical,
            requirement_code="REQ-CAE",
        ),
    )
    return result.model.to_dict()


class TestConceptAnalysisEngine:
    def test_engine_initializes_with_five_detectors(self):
        engine = ConceptAnalysisEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 5

    def test_identifies_concepts_without_modifying_internal_model(self):
        engine = ConceptAnalysisEngine()
        engine.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)
        original_snapshot = str(model_dict)

        result = engine.analyze(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )

        assert str(model_dict) == original_snapshot
        assert result.internal_model_preserved is True
        assert len(result.catalog.concepts) >= 4
        assert result.detectors_executed == 5

    def test_concepts_have_uniform_structure_and_traceability(self):
        engine = ConceptAnalysisEngine()
        engine.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        result = engine.analyze(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )

        for concept in result.catalog.concepts:
            payload = concept.to_dict()
            assert payload["concept_id"].startswith("cae://")
            assert payload["original_description"]
            assert payload["classification_pending"] is True
            assert payload["location"]["source_reference"]
            assert payload["traceability"]["document_id"] == "DOC-001"
            assert payload["traceability"]["original_preserved"] is True

    def test_identifies_items_commercial_and_technical_concepts(self):
        engine = ConceptAnalysisEngine()
        engine.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        result = engine.analyze(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )

        kinds = {concept.kind for concept in result.catalog.concepts}
        assert ConceptKind.ITEM in kinds or ConceptKind.PARTIDA in kinds
        assert ConceptKind.COMMERCIAL_ELEMENT in kinds
        assert ConceptKind.TECHNICAL_ELEMENT in kinds

    def test_catalog_prepared_for_downstream_engines(self):
        engine = ConceptAnalysisEngine()
        engine.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        result = engine.analyze(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )

        catalog = result.catalog
        assert catalog.material_classification_prepared is True
        assert catalog.service_classification_prepared is True
        assert catalog.normalization_prepared is True
        assert engine.material_classification_integration.is_prepared is True
        assert engine.service_classification_integration.is_prepared is True
        assert engine.normalization_integration.is_prepared is True

    def test_rejects_invalid_internal_model(self):
        engine = ConceptAnalysisEngine()
        engine.initialize()

        with pytest.raises(InternalModelAccessError):
            engine.analyze(
                ConceptAnalysisRequest(
                    process_id=uuid4(),
                    internal_model={"model_id": "invalid"},
                ),
            )

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        engine = ConceptAnalysisEngine(config_provider=config)
        engine.initialize()

        settings = config.classification().concept_analysis
        assert settings.enabled is True
        assert settings.item_detector_enabled is True


class TestConceptAnalysisIntegration:
    def test_service_executes_through_pipeline(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        result = service.analyze_concepts(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
                codigo_req="REQ-CAE",
            ),
        )

        assert len(result.catalog.concepts) >= 1
        assert service.concept_analysis_engine is not None
        assert service.concept_analysis_engine.catalog_store.count() == 1

    def test_pipeline_registers_concept_analysis_as_first_functional_stage(self):
        service = ClassificationService()
        service.initialize()
        snapshot = ClassificationPipeline.build_snapshot(service.component_registry)
        concept_stage = next(
            item for item in snapshot if item["phase"] == ClassificationPhase.ANALISIS_CONCEPTOS.value
        )
        assert concept_stage["component_name"] == "concept_analysis_engine"
        assert concept_stage["component_registered"] is True
        assert concept_stage["component_ready"] is True
        assert ClassificationPipeline.concept_analysis_phase() == ClassificationPhase.ANALISIS_CONCEPTOS

    def test_records_state_and_events(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ClassificationService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        service.analyze_concepts(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )

        process = state_manager.get_process(process_id)
        assert process is not None
        assert process.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cae(self):
        service = ClassificationService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_no_direct_imports_from_comprehension_in_classification_package(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.classification")
        forbidden = ("reception", "documents", "context", "communication", "comprehension")
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            package.__path__,
            prefix=package.__name__ + ".",
        ):
            module = importlib.import_module(modname)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            content = Path(source).read_text(encoding="utf-8")
            for other in forbidden:
                assert f"zovrake_motor.{other}" not in content

    def test_respects_max_concepts_configuration(self):
        config = ConfigurationProvider(
            ConfigurationProvider.default().configuration,
        )
        limited = ConceptAnalysisSettings(max_concepts_per_process=1)
        from dataclasses import replace

        motor_config = replace(
            config.configuration,
            classification=replace(
                config.classification(),
                concept_analysis=limited,
            ),
        )
        config = ConfigurationProvider(motor_config)
        engine = ConceptAnalysisEngine(config_provider=config)
        engine.initialize()
        process_id = uuid4()
        model_dict = build_internal_model_dict(process_id=process_id)

        result = engine.analyze(
            ConceptAnalysisRequest(
                process_id=process_id,
                internal_model=model_dict,
            ),
        )

        assert len(result.catalog.concepts) == 1
        assert any(incident.severity == "warning" for incident in result.incidents)
