"""Enumeraciones del Performance Optimization & Scalability Framework."""

from __future__ import annotations

from enum import Enum


class OptimizationStrategy(str, Enum):
    """Estrategias de optimización preparadas."""

    PIPELINE_FLOW = "flujo_pipeline"
    RESOURCE_USAGE = "uso_recursos"
    ASYNC_QUEUE = "cola_asincrona"
    REUSE_SAFE = "reutilizacion_segura"
    HORIZONTAL_SCALE = "escalado_horizontal"
    VERTICAL_SCALE = "escalado_vertical"


class ScalabilityMode(str, Enum):
    """Modos de escalabilidad preparados."""

    SINGLE_NODE = "nodo_unico"
    HORIZONTAL_PREPARED = "horizontal_preparado"
    VERTICAL_PREPARED = "vertical_preparado"
    ENTERPRISE_PREPARED = "empresarial_preparado"


class ResourceKind(str, Enum):
    """Tipos de recursos lógicos monitoreados."""

    MEMORY = "memoria"
    CPU = "cpu"
    TEMP_STORAGE = "almacenamiento_temporal"
    SHARED = "recursos_compartidos"
