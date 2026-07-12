"""
Pipeline Interno oficial del Motor Inteligente.

Define el recorrido secuencial de una solicitud sin ejecutar lógica de negocio.
"""

from __future__ import annotations

from typing import Any

from zovrake_motor.processing.enums import PipelineStageType
from zovrake_motor.processing.stages import PipelineStageDefinition, StageRegistry


class InternalPipeline:
    """
    Pipeline oficial administrado exclusivamente por el Coordinator.

    Recepción → Validación → Preparación → Coordinación → Procesamiento
    → Respuesta → Finalización
    """

    DEFAULT_STAGES: tuple[PipelineStageDefinition, ...] = (
        PipelineStageDefinition(PipelineStageType.RECEPCION, "Recepción", 1, "reception"),
        PipelineStageDefinition(PipelineStageType.VALIDACION, "Validación", 2, "reception"),
        PipelineStageDefinition(PipelineStageType.PREPARACION, "Preparación", 3, "context"),
        PipelineStageDefinition(PipelineStageType.COORDINACION, "Coordinación", 4, None),
        PipelineStageDefinition(PipelineStageType.PROCESAMIENTO, "Procesamiento", 5, "processing"),
        PipelineStageDefinition(PipelineStageType.RESPUESTA, "Respuesta", 6, "communication"),
        PipelineStageDefinition(PipelineStageType.FINALIZACION, "Finalización", 7, "states"),
    )

    def __init__(self, registry: StageRegistry | None = None) -> None:
        self._registry = registry or StageRegistry(self.DEFAULT_STAGES)

    @property
    def registry(self) -> StageRegistry:
        return self._registry

    @property
    def stages(self) -> tuple[PipelineStageDefinition, ...]:
        return self._registry.stages

    def ordered_stage_types(self) -> tuple[PipelineStageType, ...]:
        return self._registry.ordered_stage_types()

    def first_stage(self) -> PipelineStageType:
        return self._registry.first_stage()

    def next_stage(self, current: PipelineStageType) -> PipelineStageType | None:
        return self._registry.next_stage(current)

    def with_additional_stage(self, definition: PipelineStageDefinition) -> InternalPipeline:
        """Incorpora una nueva etapa respetando la estructura existente."""
        return InternalPipeline(self._registry.register(definition))

    def snapshot(self) -> list[dict[str, Any]]:
        return [stage.to_dict() for stage in self.stages]
