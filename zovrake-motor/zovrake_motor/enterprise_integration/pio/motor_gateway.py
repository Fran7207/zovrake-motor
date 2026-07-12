"""Gateway hacia el Motor Inteligente como unidad única — sin acoplamiento interno."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class MotorUnitGateway:
    """
    Puente preparatorio hacia el Motor Inteligente.

    El PIO invoca el Motor como una única unidad abstracta.
    No importa ni conoce módulos internos del Motor.
    """

    def __init__(self) -> None:
        self._prepared = False

    @property
    def is_prepared(self) -> bool:
        return self._prepared

    def initialize(self) -> None:
        self._prepared = True

    def invoke_prepared(
        self,
        *,
        process_id: UUID,
        codigo_req: str,
        operation: str,
    ) -> dict[str, Any]:
        """Prepara invocación futura — sin ejecutar el Motor en 8.3."""
        return {
            "invoked": False,
            "prepared": True,
            "process_id": str(process_id),
            "codigo_req": codigo_req,
            "operation": operation,
            "accesses_motor_internals": False,
            "executes_intelligent_analysis": False,
            "message": "Invocación del Motor preparada — sin ejecución en esta etapa",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "prepared": self._prepared,
            "accesses_motor_internals": False,
            "executes_intelligent_analysis": False,
        }
