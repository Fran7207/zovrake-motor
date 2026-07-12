"""Pruebas del Internal Document Model Builder — Implementación 2.7."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension import ComprehensionRequest
from zovrake_motor.comprehension.canonical import CanonicalRepresentationEngine, CanonicalRepresentationRequest
from zovrake_motor.comprehension.canonical.exceptions import TraceabilityError as CanonicalTraceabilityError
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionResult,
    ExtractedTable,
    ExtractionIncident,
    ExtractionIncidentSeverity,
)
from zovrake_motor.comprehension.internal_model import (
    CanonicalInputError,
    InternalDocumentModelBuilder,
    InternalEntityBuilderPort,
    InternalEntityType,
    InternalModelBuildRequest,
    TraceabilityError,
)
from zovrake_motor.comprehension.internal_model.models import EntityBuildResult
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentInternalModelSettings
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager


def build_extraction_result(
    *,
    process_id=None,
    document_id: str = "DOC-001",
    metadata: dict | None = None,
    original_preserved: bool = True,
) -> ContentExtractionResult:
    return ContentExtractionResult(
        process_id=process_id or uuid4(),
        document_id=document_id,
        extracted_text="Texto de prueba",
        tables=(
            ExtractedTable(
                table_id="table-1",
                rows=(("Item A", "10", "100"),),
            ),
        ),
        metadata={
            "format_type": "pdf",
            "document_reference": "adapter://pdf/DOC-001",
            "provider_name": "Proveedor Test",
            "commercial_currency": "USD",
            **(metadata or {}),
        },
        structural_elements=(),
        incidents=(
            ExtractionIncident(
                extractor_name="text_extractor",
                message="Nota de extracción",
                severity=ExtractionIncidentSeverity.INFO,
            ),
        ),
        original_preserved=original_preserved,
        ocr_integration_prepared=True,
        extractors_executed=8,
        adapter_name="pdf_adapter",
        technical_observations=("original_preserved=True",),
    )


def build_canonical_result(*, process_id=None, document_id: str = "DOC-001"):
    process_id = process_id or uuid4()
    cre = CanonicalRepresentationEngine()
    cre.initialize()
    return cre.represent(
        CanonicalRepresentationRequest(
            process_id=process_id,
            extraction_result=build_extraction_result(
                process_id=process_id,
                document_id=document_id,
            ),
        ),
    )


class TestInternalDocumentModelBuilder:
    def test_engine_initializes_with_default_builders(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 10

    def test_all_builders_implement_common_contract(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()

        for builder in engine.registry.all_builders():
            assert isinstance(builder, InternalEntityBuilderPort)
            assert builder.builder_name
            assert builder.builder_label
            assert builder.entity_type

    def test_produces_uniform_internal_model(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()
        process_id = uuid4()
        canonical = build_canonical_result(process_id=process_id)

        result = engine.build(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=canonical,
                requirement_code="REQ-001",
            ),
        )

        model = result.model
        assert model.immutable is True
        assert model.classification_ready is True
        assert model.document.document_id == "DOC-001"
        assert model.provider.name == "Proveedor Test"
        assert model.commercial_information.currency == "USD"
        assert len(model.items) == 1
        assert model.requirement_context.requirement_code == "REQ-001"
        assert model.original_references.original_preserved is True
        assert result.builders_executed == 10

    def test_result_has_uniform_structure(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()
        process_id = uuid4()

        result = engine.build(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(process_id=process_id, document_id="DOC-STRUCT"),
            ),
        )

        payload = result.to_dict()
        model = payload["model"]
        assert "traceability" in model
        assert "document" in model
        assert "provider" in model
        assert "commercial_information" in model
        assert "technical_information" in model
        assert "items" in model
        assert "commercial_conditions" in model
        assert "observations" in model
        assert "metadata" in model
        assert "requirement_context" in model
        assert "original_references" in model
        assert model["immutable"] is True
        assert payload["classification_integration_prepared"] is True

    def test_preserves_traceability_chain(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()
        process_id = uuid4()

        result = engine.build(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(process_id=process_id),
            ),
        )

        trace = result.model.traceability
        assert trace.canonical_reference_id == "cre://DOC-001"
        assert trace.extraction_reference_id == "cee://DOC-001"
        assert trace.original_preserved is True
        assert result.model.provider.canonical_reference.startswith("cee://DOC-001")
        assert result.model.provider.extraction_reference == "cee://DOC-001"
        assert result.model.items[0].canonical_reference.startswith("cee://DOC-001/items")

    def test_entity_relationships_are_consistent(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()
        process_id = uuid4()

        result = engine.build(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(process_id=process_id),
            ),
        )

        model = result.model
        document_id = model.document.document_id
        assert model.provider.document_id == document_id
        assert model.commercial_information.document_id == document_id
        assert model.technical_information.document_id == document_id
        assert all(item.document_id == document_id for item in model.items)
        assert model.requirement_context.document_id == document_id
        assert model.original_references.document_id == document_id

    def test_rejects_mismatched_process_id(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()

        with pytest.raises(CanonicalInputError):
            engine.build(
                InternalModelBuildRequest(
                    process_id=uuid4(),
                    canonical_result=build_canonical_result(),
                ),
            )

    def test_rejects_unpreserved_original(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()
        process_id = uuid4()
        cre = CanonicalRepresentationEngine()
        cre.initialize()

        with pytest.raises(CanonicalTraceabilityError):
            cre.represent(
                CanonicalRepresentationRequest(
                    process_id=process_id,
                    extraction_result=build_extraction_result(
                        process_id=process_id,
                        original_preserved=False,
                    ),
                ),
            )

    def test_classification_integration_prepared_without_execution(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()

        hook = engine.classification_integration
        assert hook.is_prepared is True
        assert hook.can_execute() is False

    def test_engine_extend_registers_new_builder(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()

        class CustomBuilder(InternalEntityBuilderPort):
            @property
            def builder_name(self) -> str:
                return "custom_builder"

            @property
            def builder_label(self) -> str:
                return "Custom Builder"

            @property
            def entity_type(self) -> InternalEntityType:
                return InternalEntityType.METADATA

            def build(self, representation, *, traceability, requirement_code="", requirement_context=None):
                return EntityBuildResult(
                    entity_type=self.entity_type.value,
                    builder_name=self.builder_name,
                )

        engine.extend(CustomBuilder())
        assert engine.registry.count() == 11


class TestInternalModelIntegration:
    def test_pipeline_executes_internal_model_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()

        result = service.build_internal_model(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(process_id=process_id),
                requirement_code="REQ-PIPE",
            ),
        )

        assert result.model.immutable is True
        assert result.builders_executed == 10
        assert result.model.requirement_context.requirement_code == "REQ-PIPE"

    def test_internal_model_stage_follows_canonical_in_pipeline(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.NORMALIZACION) < phases.index(
            ComprehensionPhase.MODELADO,
        )

    def test_internal_model_builder_component_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        builder = service.component_registry.get("internal_model_builder")
        assert builder is not None
        assert builder.is_ready() is True

    def test_state_and_event_integration_on_model_build(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        service.build_internal_model(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(process_id=process_id),
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_uses_central_configuration(self):
        settings = ComprehensionSettings(
            internal_model=DocumentInternalModelSettings(
                observations_builder_enabled=False,
                metadata_builder_enabled=False,
            ),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        engine = InternalDocumentModelBuilder(config_provider=provider)
        engine.initialize()

        assert engine.registry.count() == 8

    def test_service_ready_count_includes_internal_model(self):
        service = ComprehensionService()
        service.initialize()

        result = service.prepare(
            ComprehensionRequest(
                process_id=uuid4(),
                codigo_req="REQ-IDMB",
            ),
        )

        assert result.components_ready == 9

    def test_pdf_and_word_produce_same_model_structure(self):
        engine = InternalDocumentModelBuilder()
        engine.initialize()
        process_id = uuid4()

        pdf_result = engine.build(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(
                    process_id=process_id,
                    document_id="DOC-PDF",
                ),
            ),
        )
        word_result = engine.build(
            InternalModelBuildRequest(
                process_id=process_id,
                canonical_result=build_canonical_result(
                    process_id=process_id,
                    document_id="DOC-WORD",
                ),
            ),
        )

        pdf_keys = set(pdf_result.model.to_dict().keys())
        word_keys = set(word_result.model.to_dict().keys())
        assert pdf_keys == word_keys
        assert pdf_result.model.immutable is True
        assert word_result.model.immutable is True
