"""Contratos para módulos futuros — inyección de dependencias."""

from __future__ import annotations

from zovrake_motor.models.ports import ModulePort

# Módulos base — Implementación 1.4
BASE_MODULES: tuple[str, ...] = (
    "reception",
    "documents",
    "context",
    "states",
    "events",
    "communication",
)

# Módulos planificados — referencia arquitectónica completa
PLANNED_MODULES: tuple[str, ...] = (
    *BASE_MODULES,
    "comprehension",
    "classification",
    "comparative_tables",
    "intelligent_analysis",
    "enterprise_integration",
    "processing",
)

__all__ = ["BASE_MODULES", "ModulePort", "PLANNED_MODULES"]
