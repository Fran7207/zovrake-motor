"""
Configuración central del Motor Inteligente ZOVRAKE.

MotorSettings se mantiene como alias de compatibilidad hacia GeneralSettings.
"""

from __future__ import annotations

from zovrake_motor.config.categories.general import GeneralSettings

MotorSettings = GeneralSettings

__all__ = ["GeneralSettings", "MotorSettings"]
