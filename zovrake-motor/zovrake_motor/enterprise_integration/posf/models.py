"""Modelos inmutables del POSF — optimización y escalabilidad."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.posf.enums import (
    OptimizationStrategy,
    ResourceKind,
    ScalabilityMode,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class OptimizationHint:
    """Recomendación de optimización — no altera el flujo funcional."""

    hint_id: str
    process_id: UUID | None
    strategy: OptimizationStrategy
    component: str
    message: str
    recorded_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        process_id: UUID | None,
        strategy: OptimizationStrategy,
        component: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> OptimizationHint:
        return cls(
            hint_id=str(uuid4()),
            process_id=process_id,
            strategy=strategy,
            component=component,
            message=message,
            recorded_at=utc_now(),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hint_id": self.hint_id,
            "process_id": str(self.process_id) if self.process_id is not None else None,
            "strategy": self.strategy.value,
            "component": self.component,
            "message": self.message,
            "recorded_at": self.recorded_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ResourceUsageSnapshot:
    """Instantánea lógica de uso de recursos — sin dependencia del SO."""

    kind: ResourceKind
    units: int
    component: str
    recorded_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "units": self.units,
            "component": self.component,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass(frozen=True)
class ScalabilityReadiness:
    """Preparación para escalado empresarial futuro."""

    mode: ScalabilityMode
    horizontal_prepared: bool
    vertical_prepared: bool
    load_balancing_prepared: bool
    auto_scaling_prepared: bool
    multi_node_prepared: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "horizontal_prepared": self.horizontal_prepared,
            "vertical_prepared": self.vertical_prepared,
            "load_balancing_prepared": self.load_balancing_prepared,
            "auto_scaling_prepared": self.auto_scaling_prepared,
            "multi_node_prepared": self.multi_node_prepared,
        }
