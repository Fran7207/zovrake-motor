"""Servicio del módulo de Gestión de Estados — fachada sobre StateManager."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager
from zovrake_motor.states.models import ProcessStateRecord
from zovrake_motor.states.port import StatesPort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class StateService(ConfigurationAccessible, ModulePort, StatesPort):
    """
    Módulo de Gestión de Estados.

    Delega en StateManager — los cambios de estado deben solicitarse
    exclusivamente a través del Coordinator.
    """

    MODULE_NAME = "states"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        self._manager = state_manager or StateManager()
        self._initialized = False

    @property
    def state_manager(self) -> StateManager:
        return self._manager

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._initialized = True

    def create_process(self, process_id: UUID, codigo_req: str) -> ProcessStateRecord:
        return self._manager.create_process(process_id, codigo_req)

    def get(self, process_id: UUID) -> ProcessStateRecord | None:
        return self._manager.get_process(process_id)

    def transition(self, process_id: UUID, to_state: MotorState, reason: str) -> ProcessStateRecord:
        return self._manager.update_state(process_id, to_state, reason)
