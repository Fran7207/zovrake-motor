"""Coordinador central del Motor Inteligente."""

from zovrake_motor.coordinator.coordinator import MotorCoordinator
from zovrake_motor.coordinator.enums import (
    CoordinationPhase,
    CoordinatorState,
    ModuleLifecycleState,
)
from zovrake_motor.coordinator.models import CoordinationProcess, CoordinationResult
from zovrake_motor.coordinator.module_administrator import (
    ModuleAdministrator,
    ModuleDiscoveryResult,
    ModuleStatus,
)
from zovrake_motor.coordinator.pipeline import CoordinationPipeline, PipelineStage
from zovrake_motor.coordinator.ports import BASE_MODULES, ModulePort, PLANNED_MODULES
from zovrake_motor.coordinator.registry import ModuleRegistry

__all__ = [
    "BASE_MODULES",
    "CoordinationPhase",
    "CoordinationPipeline",
    "CoordinationProcess",
    "CoordinationResult",
    "CoordinatorState",
    "ModuleAdministrator",
    "ModuleDiscoveryResult",
    "ModuleLifecycleState",
    "ModulePort",
    "ModuleRegistry",
    "ModuleStatus",
    "MotorCoordinator",
    "PLANNED_MODULES",
    "PipelineStage",
]
