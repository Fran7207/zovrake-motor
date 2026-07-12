"""
Punto de entrada del Motor Inteligente ZOVRAKE.

Implementación 1.10 — Núcleo certificado (Prompt Maestro 3).
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import (
    ClassificationService,
    CommunicationService,
    ComprehensionService,
    ContextService,
    DocumentService,
    EnterpriseIntegrationService,
    EventService,
    MotorCoordinator,
    ReceptionService,
    StateService,
    __version__,
)
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


def _create_base_modules(
    config: ConfigurationProvider,
    state_manager: StateManager,
    event_manager: EventManager,
) -> list:
    return [
        ReceptionService(config_provider=config),
        DocumentService(config_provider=config),
        ContextService(config_provider=config),
        StateService(config_provider=config, state_manager=state_manager),
        EventService(config_provider=config, event_manager=event_manager),
        CommunicationService(config_provider=config),
    ]


def _create_planned_modules(
    config: ConfigurationProvider,
    state_manager: StateManager,
    event_manager: EventManager,
) -> list:
    return [
        ComprehensionService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        ),
        ClassificationService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        ),
        EnterpriseIntegrationService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        ),
    ]


def main() -> int:
    config = ConfigurationProvider.default()
    state_manager = StateManager()
    event_manager = EventManager(
        max_events_per_process=config.events().max_events_in_memory,
    )
    coordinator = MotorCoordinator(
        config_provider=config,
        state_manager=state_manager,
        event_manager=event_manager,
    )

    for service in _create_base_modules(config, state_manager, event_manager):
        coordinator.register_module(service)

    for service in _create_planned_modules(config, state_manager, event_manager):
        coordinator.register_module(service)

    coordinator.initialize_modules()
    coordinator.prepare_modules()

    print(f"{config.service_name()} v{config.service_version()} iniciado correctamente.")
    print(f"Paquete: zovrake_motor v{__version__}")
    print(f"Ambiente: {config.environment().value}")
    print(f"Coordinator: {coordinator.state.value}")
    print(f"Módulos registrados: {coordinator.module_administrator.count()}")
    print(f"Módulos base válidos: {coordinator.validate_base_modules()}")
    print(f"Estados oficiales: {len(state_manager.lifecycle.OFFICIAL_STATES)}")
    print(f"EMS inicializado: {event_manager.count()} eventos")

    if coordinator.is_ready():
        result = coordinator.coordinate()
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
