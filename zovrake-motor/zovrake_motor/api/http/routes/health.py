"""Rutas REST de salud del sistema."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from zovrake_motor.api.bootstrap import MotorApiRuntime
from zovrake_motor.api.http.envelope import ApiResponseEnvelope

router = APIRouter(prefix="/health", tags=["health"])


def get_runtime(request: Request) -> MotorApiRuntime:
    return request.app.state.runtime


@router.get("/motor", response_model=ApiResponseEnvelope)
def health_motor(runtime: MotorApiRuntime = Depends(get_runtime)) -> ApiResponseEnvelope:
    ready = runtime.integration_api.is_available()
    return ApiResponseEnvelope.service_message(
        status="available" if ready else "unavailable",
        message="Motor Inteligente disponible" if ready else "Motor no disponible",
        success=ready,
        result={
            "motor_ready": ready,
            "coordinator_ready": runtime.coordinator.is_ready(),
            "enterprise_integration_available": runtime.enterprise_integration.is_available(),
        },
    )


@router.get("/coordinator", response_model=ApiResponseEnvelope)
def health_coordinator(runtime: MotorApiRuntime = Depends(get_runtime)) -> ApiResponseEnvelope:
    ready = runtime.coordinator.is_ready()
    return ApiResponseEnvelope.service_message(
        status="ready" if ready else "not_ready",
        message="Coordinator operativo" if ready else "Coordinator no operativo",
        success=ready,
        result={
            "coordinator_ready": ready,
            "coordinator_state": runtime.coordinator.state.value,
            "modules_registered": runtime.coordinator.module_administrator.count(),
            "base_modules_valid": runtime.coordinator.validate_base_modules(),
        },
    )
