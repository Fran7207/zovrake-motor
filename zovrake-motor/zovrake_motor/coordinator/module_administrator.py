"""
Administrador central de módulos del Motor Inteligente.

El Coordinator delega en este componente el registro, descubrimiento,
validación y ciclo de vida de módulos — sin ejecutar lógica de negocio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.coordinator.enums import ModuleLifecycleState
from zovrake_motor.coordinator.exceptions import ModuleNotAvailableError, ModuleNotFoundError
from zovrake_motor.coordinator.ports import BASE_MODULES, PLANNED_MODULES, ModulePort
from zovrake_motor.coordinator.registry import ModuleRegistry


@dataclass(frozen=True)
class ModuleStatus:
    """Estado administrativo de un módulo registrado."""

    name: str
    lifecycle_state: ModuleLifecycleState
    is_registered: bool
    is_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "lifecycle_state": self.lifecycle_state.value,
            "is_registered": self.is_registered,
            "is_available": self.is_available,
        }


@dataclass(frozen=True)
class ModuleDiscoveryResult:
    """Resultado del descubrimiento de módulos disponibles."""

    registered: tuple[str, ...]
    base_modules: tuple[str, ...]
    missing_base: tuple[str, ...]
    planned_modules: tuple[str, ...]
    missing_planned: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "registered": list(self.registered),
            "base_modules": list(self.base_modules),
            "missing_base": list(self.missing_base),
            "planned_modules": list(self.planned_modules),
            "missing_planned": list(self.missing_planned),
        }


class ModuleAdministrator:
    """
    Administrador de módulos internos del Motor.

    Recibe módulos mediante composición o inyección de dependencias.
    No crea instancias de módulos ni ejecuta procesamiento.
    """

    def __init__(self, registry: ModuleRegistry | None = None) -> None:
        self._registry = registry or ModuleRegistry()
        self._lifecycle: dict[str, ModuleLifecycleState] = {}
        self._sync_lifecycle_from_registry()

    def _sync_lifecycle_from_registry(self) -> None:
        for name in self._registry.registered_names():
            module = self._registry.get(name)
            if module is None:
                continue
            if module.is_available():
                self._lifecycle[name] = ModuleLifecycleState.DISPONIBLE
            else:
                self._lifecycle[name] = ModuleLifecycleState.REGISTRADO

    @property
    def registry(self) -> ModuleRegistry:
        return self._registry

    def register(self, module: ModulePort) -> None:
        """Registra un módulo de forma independiente."""
        self._registry.register(module)
        if module.is_available():
            self._lifecycle[module.module_name] = ModuleLifecycleState.DISPONIBLE
        else:
            self._lifecycle[module.module_name] = ModuleLifecycleState.REGISTRADO

    def get(self, name: str) -> ModulePort | None:
        return self._registry.get(name)

    def require(self, name: str) -> ModulePort:
        module = self.get(name)
        if module is None:
            raise ModuleNotFoundError(f"Módulo no registrado: {name}")
        return module

    def is_registered(self, name: str) -> bool:
        return self._registry.is_registered(name)

    def is_available(self, name: str) -> bool:
        if not self.is_registered(name):
            return False
        module = self.require(name)
        lifecycle = self._lifecycle.get(name, ModuleLifecycleState.REGISTRADO)
        return module.is_available() and lifecycle in {
            ModuleLifecycleState.DISPONIBLE,
            ModuleLifecycleState.PREPARADO,
        }

    def lifecycle_state(self, name: str) -> ModuleLifecycleState:
        if not self.is_registered(name):
            return ModuleLifecycleState.REGISTRADO
        return self._lifecycle.get(name, ModuleLifecycleState.REGISTRADO)

    def list_modules(self) -> list[str]:
        return self._registry.registered_names()

    def discover(self) -> ModuleDiscoveryResult:
        registered = tuple(self.list_modules())
        missing_base = tuple(name for name in BASE_MODULES if name not in registered)
        missing_planned = tuple(name for name in PLANNED_MODULES if name not in registered)
        return ModuleDiscoveryResult(
            registered=registered,
            base_modules=BASE_MODULES,
            missing_base=missing_base,
            planned_modules=PLANNED_MODULES,
            missing_planned=missing_planned,
        )

    def validate_base_modules(self) -> bool:
        discovery = self.discover()
        if discovery.missing_base:
            return False
        return all(self.is_available(name) for name in BASE_MODULES)

    def initialize_module(self, name: str) -> None:
        module = self.require(name)
        if not module.is_available():
            module.initialize()
        self._lifecycle[name] = ModuleLifecycleState.DISPONIBLE

    def initialize_all(self) -> None:
        for name in self.list_modules():
            self.initialize_module(name)

    def prepare_module(self, name: str) -> None:
        if not self.is_available(name):
            raise ModuleNotAvailableError(f"Módulo no disponible para preparación: {name}")
        self._lifecycle[name] = ModuleLifecycleState.PREPARADO

    def prepare_all(self) -> None:
        for name in self.list_modules():
            if self.is_available(name):
                self.prepare_module(name)

    def finalize_module(self, name: str) -> None:
        if not self.is_registered(name):
            raise ModuleNotFoundError(f"Módulo no registrado: {name}")
        self._lifecycle[name] = ModuleLifecycleState.FINALIZADO

    def finalize_all(self) -> None:
        for name in self.list_modules():
            self.finalize_module(name)

    def get_status(self, name: str) -> ModuleStatus:
        return ModuleStatus(
            name=name,
            lifecycle_state=self.lifecycle_state(name),
            is_registered=self.is_registered(name),
            is_available=self.is_available(name),
        )

    def all_statuses(self) -> list[ModuleStatus]:
        return [self.get_status(name) for name in self.list_modules()]

    def count(self) -> int:
        return self._registry.count()
