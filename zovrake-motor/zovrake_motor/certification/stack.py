"""Utilidades para construir el stack certificable del núcleo."""

from __future__ import annotations

from zovrake_motor.communication import CommunicationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.context import ContextService
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.documents import DocumentService
from zovrake_motor.events import EventManager, EventService
from zovrake_motor.reception import ReceptionService
from zovrake_motor.states import StateManager, StateService


def build_certified_stack() -> tuple[MotorCoordinator, ConfigurationProvider, StateManager, EventManager]:
    """Construye el stack completo del núcleo para validación."""
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

    services = [
        ReceptionService(config_provider=config),
        DocumentService(config_provider=config),
        ContextService(config_provider=config),
        StateService(config_provider=config, state_manager=state_manager),
        EventService(config_provider=config, event_manager=event_manager),
        CommunicationService(config_provider=config),
    ]

    for service in services:
        service.initialize()
        coordinator.register_module(service)

    coordinator.prepare_modules()
    return coordinator, config, state_manager, event_manager
