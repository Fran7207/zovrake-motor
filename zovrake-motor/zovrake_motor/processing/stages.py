"""Definición y registro de etapas del Pipeline Interno."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zovrake_motor.processing.enums import PipelineStageType
from zovrake_motor.processing.exceptions import PipelineError


@dataclass(frozen=True)
class PipelineStageDefinition:
    """
    Definición inmutable de una etapa del Pipeline.

    Cada etapa tiene una única responsabilidad y un orden secuencial fijo.
    """

    stage: PipelineStageType
    label: str
    order: int
    associated_module: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "label": self.label,
            "order": self.order,
            "associated_module": self.associated_module,
        }


class StageRegistry:
    """
    Registro extensible de etapas del Pipeline.

    Permite incorporar nuevas etapas sin modificar las existentes.
    """

    def __init__(self, stages: tuple[PipelineStageDefinition, ...] | None = None) -> None:
        self._stages = stages or ()
        if self._stages:
            self._validate()

    @property
    def stages(self) -> tuple[PipelineStageDefinition, ...]:
        return self._stages

    def register(self, definition: PipelineStageDefinition) -> StageRegistry:
        """Retorna un nuevo registro con la etapa adicional."""
        return StageRegistry((*self._stages, definition))

    def ordered_stage_types(self) -> tuple[PipelineStageType, ...]:
        return tuple(stage.stage for stage in self._stages)

    def get_definition(self, stage: PipelineStageType) -> PipelineStageDefinition:
        for definition in self._stages:
            if definition.stage == stage:
                return definition
        raise PipelineError(f"Etapa no registrada: {stage.value}")

    def next_stage(self, current: PipelineStageType) -> PipelineStageType | None:
        ordered = self.ordered_stage_types()
        try:
            index = ordered.index(current)
        except ValueError as exc:
            raise PipelineError(f"Etapa no registrada: {current.value}") from exc
        if index + 1 >= len(ordered):
            return None
        return ordered[index + 1]

    def first_stage(self) -> PipelineStageType:
        if not self._stages:
            raise PipelineError("El Pipeline no tiene etapas registradas")
        return self._stages[0].stage

    def _validate(self) -> None:
        orders = [stage.order for stage in self._stages]
        if len(orders) != len(set(orders)):
            raise PipelineError("Las etapas del Pipeline deben tener órdenes únicos")

        if orders != sorted(orders):
            raise PipelineError("Las etapas del Pipeline deben estar ordenadas secuencialmente")

        stage_types = [stage.stage for stage in self._stages]
        if len(stage_types) != len(set(stage_types)):
            raise PipelineError("Las etapas del Pipeline deben ser únicas")
