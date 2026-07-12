"""
Estructura del flujo de coordinación futuro.

Define el pipeline interno sin ejecutar procesamiento ni lógica de negocio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from zovrake_motor.coordinator.module_administrator import ModuleAdministrator


@dataclass(frozen=True)
class PipelineStage:
    """Etapa del flujo de coordinación — referencia arquitectónica."""

    module_name: str
    label: str
    order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "label": self.label,
            "order": self.order,
        }


class CoordinationPipeline:
    """
    Pipeline de coordinación del Motor Inteligente.

    Estructura preparada para orquestación futura. El Coordinator consulta
    disponibilidad de cada etapa sin invocar procesamiento.
    """

    MAIN_STAGES: tuple[PipelineStage, ...] = (
        PipelineStage("reception", "Recepción", 1),
        PipelineStage("documents", "Gestión de Documentos", 2),
        PipelineStage("context", "Gestión del Contexto", 3),
        PipelineStage("comprehension", "Comprensión Documental", 4),
        PipelineStage("classification", "Clasificación Inteligente", 5),
        PipelineStage("comparative_tables", "Generación de Cuadros Comparativos", 6),
        PipelineStage("intelligent_analysis", "Resultado del Análisis Inteligente", 7),
    )

    SUPPORTING_MODULES: tuple[str, ...] = ("states", "events")
    INTEGRATION_MODULES: tuple[str, ...] = ("communication", "enterprise_integration")

    @classmethod
    def ordered_module_names(cls) -> tuple[str, ...]:
        return tuple(stage.module_name for stage in cls.MAIN_STAGES)

    @classmethod
    def all_referenced_modules(cls) -> tuple[str, ...]:
        return (
            *cls.ordered_module_names(),
            *cls.SUPPORTING_MODULES,
            *cls.INTEGRATION_MODULES,
        )

    @classmethod
    def build_snapshot(cls, administrator: ModuleAdministrator) -> list[dict[str, Any]]:
        """Construye el estado estructural del pipeline sin ejecutar etapas."""
        snapshot: list[dict[str, Any]] = []

        for stage in cls.MAIN_STAGES:
            snapshot.append(
                {
                    **stage.to_dict(),
                    "registered": administrator.is_registered(stage.module_name),
                    "available": administrator.is_available(stage.module_name),
                    "lifecycle_state": administrator.lifecycle_state(stage.module_name).value,
                }
            )

        for module_name in (*cls.SUPPORTING_MODULES, *cls.INTEGRATION_MODULES):
            snapshot.append(
                {
                    "module_name": module_name,
                    "label": module_name.replace("_", " ").title(),
                    "order": None,
                    "registered": administrator.is_registered(module_name),
                    "available": administrator.is_available(module_name),
                    "lifecycle_state": administrator.lifecycle_state(module_name).value,
                    "role": "supporting" if module_name in cls.SUPPORTING_MODULES else "integration",
                }
            )

        return snapshot
