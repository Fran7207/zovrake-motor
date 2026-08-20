"""Gateway hacia el Motor Inteligente como unidad única — sin acoplamiento interno."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID


MotorInvocationHandler = Callable[..., dict[str, Any]]


class MotorUnitGateway:
    """
    Puente hacia el Motor Inteligente.

    El PIO invoca el Motor como una única unidad abstracta.
    No importa ni conoce módulos internos del Motor.
    La ejecución real se inyecta desde fuera de ``enterprise_integration``
    (``motor_runtime``) respetando el contrato PM8.
    """

    def __init__(self, *, invocation_handler: MotorInvocationHandler | None = None) -> None:
        self._prepared = False
        self._invocation_handler = invocation_handler

    @property
    def is_prepared(self) -> bool:
        return self._prepared

    def initialize(self) -> None:
        self._prepared = True

    def bind_invocation_handler(self, handler: MotorInvocationHandler | None) -> None:
        """Inyecta el ejecutor real del Motor sin acoplar módulos prohibidos."""
        self._invocation_handler = handler

    def invoke_prepared(
    self,
    *,
    process_id: UUID,
    codigo_req: str,
    operation: str,
    document_ids: tuple[str, ...] = (),
    document_references: tuple[dict[str, Any], ...] = (),
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
        """Invoca el Motor como unidad única (handler inyectado o stub de preparación)."""
        if self._invocation_handler is not None:
            result = self._invocation_handler(
    process_id=process_id,
    codigo_req=codigo_req,
    operation=operation,
    document_ids=document_ids,
    document_references=document_references,
    metadata=dict(metadata or {}),
)


            if isinstance(result, dict):
                return {
                    "invoked": bool(result.get("invoked", result.get("executed", False))),
                    "prepared": bool(result.get("prepared", True)),
                    "executed": bool(result.get("executed", result.get("invoked", False))),
                    "process_id": str(process_id),
                    "codigo_req": codigo_req,
                    "operation": operation,
                    "accesses_motor_internals": False,
                    "executes_intelligent_analysis": bool(
                        result.get("executes_intelligent_analysis", result.get("executed", False))
                    ),
                    "message": str(
                        result.get(
                            "message",
                            "Invocación del Motor ejecutada",
                        )
                    ),
                    **{
                        key: value
                        for key, value in result.items()
                        if key
                        not in {
                            "invoked",
                            "prepared",
                            "executed",
                            "process_id",
                            "codigo_req",
                            "operation",
                            "accesses_motor_internals",
                            "executes_intelligent_analysis",
                            "message",
                        }
                    },
                }

        return {
            "invoked": False,
            "prepared": True,
            "executed": False,
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
            "handler_bound": self._invocation_handler is not None,
            "accesses_motor_internals": False,
            "executes_intelligent_analysis": self._invocation_handler is not None,
        }
