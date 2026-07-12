"""Modelos compartidos del Motor Inteligente."""

from zovrake_motor.models.common import MotorRequest, MotorResponse
from zovrake_motor.models.ports import ModulePort

__all__ = [
    "ModulePort",
    "MotorRequest",
    "MotorResponse",
]
