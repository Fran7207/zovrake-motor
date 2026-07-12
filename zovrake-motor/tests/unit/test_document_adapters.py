"""Pruebas del Document Adapter Framework — Implementación 2.2."""

from __future__ import annotations

from zovrake_motor import ComprehensionService
from zovrake_motor.comprehension.adapters import (
    AdapterRegistry,
    DocumentAdapterFramework,
    DocumentAdapterPort,
    DocumentFormatType,
    ExcelDocumentAdapter,
    ImageDocumentAdapter,
    PdfDocumentAdapter,
    WordDocumentAdapter,
)
from zovrake_motor.comprehension.adapters.models import AdapterResolutionRequest
from zovrake_motor.comprehension.enums import ComprehensionPhase
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.config.categories.comprehension import ComprehensionSettings, DocumentAdapterSettings


class TestDocumentAdapterFramework:
    def test_framework_initializes_with_four_adapters(self):
        framework = DocumentAdapterFramework()
        framework.initialize()

        assert framework.is_ready()
        assert framework.registry.count() == 4
        assert framework.registry.ready_count() == 4

    def test_all_adapters_implement_common_contract(self):
        framework = DocumentAdapterFramework()
        framework.initialize()

        for adapter in framework.registry.all_adapters():
            assert isinstance(adapter, DocumentAdapterPort)
            assert adapter.adapter_name
            assert adapter.adapter_label
            assert adapter.format_type
            assert adapter.supported_extensions

    def test_registered_adapters_cover_initial_formats(self):
        framework = DocumentAdapterFramework()
        framework.initialize()

        registered = {adapter.adapter_name for adapter in framework.registry.all_adapters()}
        assert registered == {
            "pdf_adapter",
            "word_adapter",
            "excel_adapter",
            "image_adapter",
        }

    def test_resolver_requires_explicit_format(self):
        framework = DocumentAdapterFramework()
        framework.initialize()

        result = framework.resolve(
            AdapterResolutionRequest(format_type=DocumentFormatType.PDF),
        )
        assert result.resolved is False
        assert result.adapter_name == "pdf_adapter"
        assert "deshabilitado" in result.message.lower()

    def test_resolver_succeeds_when_format_enabled(self):
        config = ConfigurationProvider.default()
        settings = ComprehensionSettings(
            adapters=DocumentAdapterSettings(
                enabled=True,
                pdf_enabled=True,
            ),
        )
        from zovrake_motor.config.motor_configuration import MotorConfiguration

        provider = ConfigurationProvider(
            configuration=MotorConfiguration(comprehension=settings),
        )
        framework = DocumentAdapterFramework(config_provider=provider)
        framework.initialize()

        result = framework.resolve(
            AdapterResolutionRequest(format_type=DocumentFormatType.PDF),
        )
        assert result.resolved is True
        assert result.adapter_name == "pdf_adapter"

    def test_framework_extend_registers_additional_adapters(self):
        registry = AdapterRegistry()
        framework = DocumentAdapterFramework(registry=registry)
        framework.extend(PdfDocumentAdapter())
        framework.extend(WordDocumentAdapter())
        framework.initialize()

        assert framework.registry.count() == 2
        assert framework.registry.get(DocumentFormatType.PDF) is not None
        assert framework.registry.get(DocumentFormatType.WORD) is not None

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        framework = DocumentAdapterFramework(config_provider=config)
        framework.initialize()

        snapshot = framework.snapshot()
        assert snapshot["configuration"]["enabled"] is False
        assert snapshot["configuration"]["auto_resolution_enabled"] is False


class TestDocumentAdapterIntegration:
    def test_comprehension_service_exposes_adapter_framework(self):
        service = ComprehensionService()
        service.initialize()

        framework = service.adapter_framework
        assert framework is not None
        assert framework.is_ready()
        assert framework.registry.count() == 4

    def test_document_pipeline_includes_adaptation_stage(self):
        service = ComprehensionService()
        service.initialize()

        phases = DocumentComprehensionPipeline.ordered_phases()
        assert ComprehensionPhase.ADAPTACION in phases
        assert phases.index(ComprehensionPhase.ADAPTACION) == 2

        snapshot = service.get_document_pipeline_snapshot()
        adaptation = next(item for item in snapshot if item["phase"] == "adaptacion")
        validation = next(item for item in snapshot if item["phase"] == "validacion")
        assert validation["component_name"] == "document_validator"
        assert validation["component_ready"] is True
        assert adaptation["component_name"] == "document_adapters"
        assert adaptation["component_registered"] is True
        assert adaptation["component_ready"] is True

    def test_adapters_manager_is_ready_after_initialization(self):
        service = ComprehensionService()
        service.initialize()

        adapters = service.component_registry.get("document_adapters")
        assert adapters is not None
        assert adapters.is_ready() is True

    def test_initial_adapters_are_independent(self):
        adapters = (
            PdfDocumentAdapter(),
            WordDocumentAdapter(),
            ExcelDocumentAdapter(),
            ImageDocumentAdapter(),
        )
        names = {adapter.adapter_name for adapter in adapters}
        formats = {adapter.format_type for adapter in adapters}
        assert len(names) == 4
        assert len(formats) == 4
