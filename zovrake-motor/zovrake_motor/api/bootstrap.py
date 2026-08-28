"""Fachada pública del bootstrap de la API.

La composición concreta del runtime vive fuera de ``api`` para mantener
la capa HTTP desacoplada de los módulos internos del Motor.
"""

from __future__ import annotations

from zovrake_motor.motor_runtime.api_bootstrap import (
    MotorApiRuntime,
    build_motor_api_runtime,
)

__all__ = [
    "MotorApiRuntime",
    "build_motor_api_runtime",
]