"""Registro de módulos para composición e inyección de dependencias."""

from __future__ import annotations

from zovrake_motor.coordinator.ports import BASE_MODULES, PLANNED_MODULES, ModulePort


class ModuleRegistry:
    """
    Registro central de módulos del Motor.

    El Coordinator recibe módulos mediante composición — nunca los crea directamente.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModulePort] = {}

    def register(self, module: ModulePort) -> None:
        self._modules[module.module_name] = module

    def get(self, name: str) -> ModulePort | None:
        return self._modules.get(name)

    def is_registered(self, name: str) -> bool:
        return name in self._modules

    def registered_names(self) -> list[str]:
        return list(self._modules.keys())

    def planned_modules(self) -> tuple[str, ...]:
        return PLANNED_MODULES

    def all_planned_registered(self) -> bool:
        return all(name in self._modules for name in PLANNED_MODULES)

    def all_base_registered(self) -> bool:
        return all(name in self._modules for name in BASE_MODULES)

    def count(self) -> int:
        return len(self._modules)
