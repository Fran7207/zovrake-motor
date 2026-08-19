"""
Runtime de ejecución del Motor Inteligente para Cotizaciones.

Reside fuera de ``enterprise_integration`` para respetar el contrato PM8
(prohibición de importar módulos inteligentes desde la plataforma de integración).
"""

from __future__ import annotations

from zovrake_motor.motor_runtime.bridge import MotorExecutionBridge
from zovrake_motor.motor_runtime.cotizaciones_executor import CotizacionesAnalysisExecutor
from zovrake_motor.motor_runtime.result_registry import AnalysisResultRegistry

__all__ = [
    "AnalysisResultRegistry",
    "CotizacionesAnalysisExecutor",
    "MotorExecutionBridge",
]
