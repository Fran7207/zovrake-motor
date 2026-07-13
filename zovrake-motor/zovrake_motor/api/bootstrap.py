"""Arranque del Motor y la API oficial — Prompt Maestro 9.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor import (
    ClassificationService,
    CommunicationService,
    ComprehensionService,
    ContextService,
    DocumentService,
    EnterpriseIntegrationService,
    EventService,
    IntegrationApiService,
    MotorCoordinator,
    ReceptionService,
    StateService,
    __version__,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


@dataclass
class MotorApiRuntime:
    """Runtime compartido entre la API REST y el Coordinator del Motor."""

    config: ConfigurationProvider
    state_manager: StateManager
    event_manager: EventManager
    coordinator: MotorCoordinator
    enterprise_integration: EnterpriseIntegrationService
    integration_api: IntegrationApiService

    def initialize(self) -> None:
        for service in self._base_modules():
            self.coordinator.register_module(service)
        self.coordinator.register_module(self.enterprise_integration)
        for service in self._planned_modules():
            self.coordinator.register_module(service)
        self.coordinator.initialize_modules()
        self.coordinator.prepare_modules()
        self.integration_api.initialize()

    def _base_modules(self) -> list:
        return [
            ReceptionService(config_provider=self.config),
            DocumentService(config_provider=self.config),
            ContextService(config_provider=self.config),
            StateService(
                config_provider=self.config,
                state_manager=self.state_manager,
            ),
            EventService(
                config_provider=self.config,
                event_manager=self.event_manager,
            ),
            CommunicationService(config_provider=self.config),
        ]

    def _planned_modules(self) -> list:
        return [
            ComprehensionService(
                config_provider=self.config,
                state_manager=self.state_manager,
                event_manager=self.event_manager,
            ),
            ClassificationService(
                config_provider=self.config,
                state_manager=self.state_manager,
                event_manager=self.event_manager,
            ),
        ]

    def snapshot(self) -> dict[str, Any]:
        return {
            "motor_version": __version__,
            "coordinator_ready": self.coordinator.is_ready(),
            "integration_api_available": self.integration_api.is_available(),
            "enterprise_integration_available": self.enterprise_integration.is_available(),
            "modules_registered": self.coordinator.module_administrator.count(),
        }


def build_motor_api_runtime(
    *,
    config: ConfigurationProvider | None = None,
) -> MotorApiRuntime:
    config = config or ConfigurationProvider.default()
    state_manager = StateManager()
    event_manager = EventManager(
        max_events_per_process=config.events().max_events_in_memory,
    )
    coordinator = MotorCoordinator(
        config_provider=config,
        state_manager=state_manager,
        event_manager=event_manager,
    )
    enterprise_integration = EnterpriseIntegrationService(
        config_provider=config,
        state_manager=state_manager,
        event_manager=event_manager,
    )
    integration_api = IntegrationApiService(
        config_provider=config,
        state_manager=state_manager,
        event_manager=event_manager,
        enterprise_service=enterprise_integration,
    )
    runtime = MotorApiRuntime(
        config=config,
        state_manager=state_manager,
        event_manager=event_manager,
        coordinator=coordinator,
        enterprise_integration=enterprise_integration,
        integration_api=integration_api,
    )
    runtime.initialize()
    return runtime
