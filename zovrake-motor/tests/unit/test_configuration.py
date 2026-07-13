"""Pruebas del Sistema Centralizado de Configuración — Implementación 1.6."""

from __future__ import annotations

import importlib

import pytest

from zovrake_motor.config import (
    ConfigCategory,
    ConfigurationError,
    ConfigurationProvider,
    ConfigurationValidator,
    MotorEnvironment,
    MotorSettings,
)
from zovrake_motor.config.categories import (
    EventsSettings,
    FutureSettings,
    GeneralSettings,
)
from zovrake_motor.config.loader import ConfigurationLoader
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.communication import CommunicationService
from zovrake_motor.events import EventService
from zovrake_motor.reception import ReceptionService


class TestConfigurationProvider:
    def test_default_provider_loads_all_categories(self):
        provider = ConfigurationProvider.default()
        snapshot = provider.snapshot()

        assert provider.service_name() == "zovrake-motor"
        assert provider.service_version() == "9.4.0"
        assert provider.environment() == MotorEnvironment.DEVELOPMENT
        assert "general" in snapshot
        assert "paths" in snapshot
        assert "future" in snapshot
        assert "comprehension" in snapshot

    def test_for_environment(self):
        provider = ConfigurationProvider.for_environment(MotorEnvironment.PRODUCTION)
        assert provider.environment() == MotorEnvironment.PRODUCTION

    def test_get_category(self):
        provider = ConfigurationProvider.default()
        events = provider.get_category(ConfigCategory.EVENTS)
        assert isinstance(events, EventsSettings)

    def test_from_general_backward_compatibility(self):
        general = GeneralSettings(service_name="test-motor", service_version="9.9.9")
        provider = ConfigurationProvider.from_general(general)
        assert provider.service_name() == "test-motor"
        assert provider.service_version() == "9.9.9"

    def test_motor_settings_alias(self):
        settings = MotorSettings.default()
        assert settings.service_name == "zovrake-motor"
        assert settings.service_version == "9.4.0"


    def test_comprehension_category_available(self):
        provider = ConfigurationProvider.default()
        comprehension = provider.comprehension()
        assert comprehension.enabled is False
        assert comprehension.max_documents_per_process == 100
        assert comprehension.adapters.enabled is False
        assert comprehension.validation.enabled is False
        assert comprehension.recognition.enabled is False
        assert comprehension.extraction.enabled is False
        assert comprehension.canonical.enabled is False
        assert comprehension.internal_model.enabled is False
        assert comprehension.knowledge_index.enabled is False
        assert comprehension.knowledge_index.prevent_duplicates is True
        assert comprehension.context_integration.enabled is False
        assert comprehension.context_integration.preserve_document_immutability is True

    def test_get_comprehension_category(self):
        provider = ConfigurationProvider.default()
        comprehension = provider.get_category(ConfigCategory.COMPREHENSION)
        assert comprehension.enabled is False


class TestConfigurationValidator:
    def test_valid_configuration_passes(self):
        configuration = ConfigurationLoader.load()
        ConfigurationValidator().validate(configuration)

    def test_invalid_service_name_raises(self):
        configuration = MotorConfiguration(
            general=GeneralSettings(service_name="  "),
        )
        with pytest.raises(ConfigurationError, match="service_name"):
            ConfigurationValidator().validate(configuration)

    def test_invalid_max_events_raises(self):
        configuration = MotorConfiguration(
            events=EventsSettings(max_events_in_memory=0),
        )
        with pytest.raises(ConfigurationError, match="max_events_in_memory"):
            ConfigurationValidator().validate(configuration)


class TestFutureConfigurationStructure:
    def test_future_settings_prepared(self):
        future = FutureSettings.default()
        assert future.ocr.enabled is False
        assert future.ai.enabled is False
        assert future.api.enabled is False
        assert future.storage.enabled is False
        assert future.monitoring.enabled is False


class TestModulesUseCentralConfiguration:
    def test_module_receives_shared_provider(self):
        provider = ConfigurationProvider.default()
        reception = ReceptionService(config_provider=provider)
        events = EventService(config_provider=provider)

        assert reception.config_provider is provider
        assert events.config_provider is provider

    def test_event_service_reads_max_events_from_provider(self):
        provider = ConfigurationProvider.default()
        service = EventService(config_provider=provider)
        service.initialize()

        assert service.event_manager is not None
        assert provider.events().max_events_in_memory > 0

    def test_modules_without_provider_use_category_defaults(self):
        service = EventService()
        service.initialize()
        assert service.is_available()
        assert EventsSettings.default().max_events_in_memory > 0

    def test_no_local_configuration_constants_in_services(self):
        service_modules = (
            "zovrake_motor.reception.service",
            "zovrake_motor.documents.service",
            "zovrake_motor.context.service",
            "zovrake_motor.states.service",
            "zovrake_motor.events.service",
            "zovrake_motor.communication.service",
        )
        forbidden_patterns = ("service_version", "protocol =")

        for module_name in service_modules:
            module = importlib.import_module(module_name)
            source_file = module.__file__
            assert source_file is not None
            with open(source_file, encoding="utf-8") as fh:
                content = fh.read()
            for pattern in forbidden_patterns:
                assert pattern not in content, f"{module_name} contiene configuración local: {pattern}"

    def test_service_files_use_central_configuration(self):
        service_modules = (
            "zovrake_motor.reception.service",
            "zovrake_motor.documents.service",
            "zovrake_motor.context.service",
            "zovrake_motor.states.service",
            "zovrake_motor.events.service",
            "zovrake_motor.communication.service",
        )

        for module_name in service_modules:
            module = importlib.import_module(module_name)
            source_file = module.__file__
            assert source_file is not None
            with open(source_file, encoding="utf-8") as fh:
                content = fh.read()
            assert "ConfigurationAccessible" in content
            assert "config_provider" in content
