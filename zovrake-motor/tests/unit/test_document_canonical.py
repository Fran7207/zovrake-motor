"""Pruebas del Canonical Representation Engine — Implementación 2.6."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension import ComprehensionRequest
from zovrake_motor.comprehension.canonical import (
    CanonicalRepresentationEngine,
    CanonicalRepresentationRequest,
    CanonicalSectionTransformerPort,
    ExtractionInputError,
    TraceabilityError,
    TransformerRegistry,
)
from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import SectionTransformationResult
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.extraction.models import (
    ContentExtractionResult,
    ExtractedTable,
    ExtractionIncident,
    ExtractionIncidentSeverity,
)
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentCanonicalSettings
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


class TestCanonicalRepresentationEngine:
    def test_engine_initializes_with_default_transformers(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 7

    def test_all_transformers_implement_common_contract(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()

        for transformer in engine.registry.all_transformers():
            assert isinstance(transformer, CanonicalSectionTransformerPort)
            assert transformer.transformer_name
            assert transformer.transformer_label
            assert transformer.section_type

    def test_produces_uniform_canonical_structure(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()
        process_id = uuid4()

        result = engine.represent(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(process_id=process_id),
            ),
        )

        representation = result.representation
        assert representation.immutable is True
        assert representation.traceability.document_id == "DOC-001"
        assert representation.provider.name == "Proveedor Test"
        assert representation.commercial_information.currency == "USD"
        assert len(representation.items) == 1
        assert len(representation.observations) >= 1
        assert result.original_preserved is True
        assert result.transformers_executed == 7

    def test_result_has_uniform_structure(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()
        process_id = uuid4()

        result = engine.represent(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(process_id=process_id, document_id="DOC-STRUCT"),
            ),
        )

        payload = result.to_dict()
        rep = payload["representation"]
        assert "traceability" in rep
        assert "provider" in rep
        assert "commercial_information" in rep
        assert "technical_information" in rep
        assert "items" in rep
        assert "conditions" in rep
        assert "observations" in rep
        assert "metadata" in rep
        assert rep["immutable"] is True
        assert payload["classification_integration_prepared"] is True

    def test_preserves_traceability_references(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()
        process_id = uuid4()

        result = engine.represent(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(process_id=process_id),
            ),
        )

        traceability = result.representation.traceability
        assert traceability.extraction_reference_id == "cee://DOC-001"
        assert traceability.original_preserved is True
        assert result.representation.provider.source_reference.startswith("cee://DOC-001")
        assert result.representation.items[0].source_reference.startswith("cee://DOC-001/items")

    def test_rejects_mismatched_process_id(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()

        with pytest.raises(ExtractionInputError):
            engine.represent(
                CanonicalRepresentationRequest(
                    process_id=uuid4(),
                    extraction_result=build_extraction_result(),
                ),
            )

    def test_rejects_unpreserved_original(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(TraceabilityError):
            engine.represent(
                CanonicalRepresentationRequest(
                    process_id=process_id,
                    extraction_result=build_extraction_result(
                        process_id=process_id,
                        original_preserved=False,
                    ),
                ),
            )

    def test_classification_integration_prepared_without_execution(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()

        hook = engine.classification_integration
        assert hook.is_prepared is True
        assert hook.can_execute() is False

    def test_engine_extend_registers_new_transformer(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()

        class CustomTransformer(CanonicalSectionTransformerPort):
            @property
            def transformer_name(self) -> str:
                return "custom_transformer"

            @property
            def transformer_label(self) -> str:
                return "Custom Transformer"

            @property
            def section_type(self) -> CanonicalSectionType:
                return CanonicalSectionType.METADATA

            def transform(self, extraction_result, *, traceability):
                return SectionTransformationResult(
                    section_type=self.section_type.value,
                    transformer_name=self.transformer_name,
                )

        engine.extend(CustomTransformer())
        assert engine.registry.count() == 8


class TestCanonicalRepresentationIntegration:
    def test_pipeline_executes_canonical_stage(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()

        result = service.build_canonical_representation(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(process_id=process_id),
            ),
        )

        assert result.representation.immutable is True
        assert result.transformers_executed == 7

    def test_canonical_stage_follows_extraction_in_pipeline(self):
        phases = DocumentComprehensionPipeline.ordered_phases()
        assert phases.index(ComprehensionPhase.EXTRACCION) < phases.index(
            ComprehensionPhase.NORMALIZACION,
        )

    def test_normalizer_component_is_ready(self):
        service = ComprehensionService()
        service.initialize()

        normalizer = service.component_registry.get("normalizer")
        assert normalizer is not None
        assert normalizer.is_ready() is True

    def test_state_and_event_integration_on_representation(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()

        service.build_canonical_representation(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(process_id=process_id),
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_uses_central_configuration(self):
        settings = ComprehensionSettings(
            canonical=DocumentCanonicalSettings(
                conditions_transformer_enabled=False,
                observations_transformer_enabled=False,
            ),
        )
        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        engine = CanonicalRepresentationEngine(config_provider=provider)
        engine.initialize()

        assert engine.registry.count() == 5

    def test_service_ready_count_includes_canonical(self):
        service = ComprehensionService()
        service.initialize()

        result = service.prepare(
            ComprehensionRequest(
                process_id=uuid4(),
                codigo_req="REQ-CRE",
            ),
        )

        assert result.components_ready == 9

    def test_pdf_and_excel_produce_same_structure(self):
        engine = CanonicalRepresentationEngine()
        engine.initialize()
        process_id = uuid4()

        pdf_result = engine.represent(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(
                    process_id=process_id,
                    metadata={"format_type": "pdf"},
                ),
            ),
        )
        excel_result = engine.represent(
            CanonicalRepresentationRequest(
                process_id=process_id,
                extraction_result=build_extraction_result(
                    process_id=process_id,
                    document_id="DOC-XLS",
                    metadata={"format_type": "xlsx", "document_reference": "adapter://excel/DOC-XLS"},
                ),
            ),
        )

        pdf_keys = set(pdf_result.representation.to_dict().keys())
        excel_keys = set(excel_result.representation.to_dict().keys())
        assert pdf_keys == excel_keys
        assert pdf_result.representation.immutable is True
        assert excel_result.representation.immutable is True
