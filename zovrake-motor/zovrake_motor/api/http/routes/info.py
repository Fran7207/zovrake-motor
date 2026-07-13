"""Rutas REST de información del servicio."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from zovrake_motor import __version__
from zovrake_motor.api.bootstrap import MotorApiRuntime
from zovrake_motor.api.governance import governance_snapshot
from zovrake_motor.api.http.envelope import ApiResponseEnvelope

router = APIRouter(prefix="/info", tags=["info"])


def get_runtime(request: Request) -> MotorApiRuntime:
    return request.app.state.runtime


@router.get("/version", response_model=ApiResponseEnvelope)
def info_version() -> ApiResponseEnvelope:
    governance = governance_snapshot()
    return ApiResponseEnvelope.service_message(
        status="ok",
        message="Versión del servicio",
        success=True,
        result={
            "motor_version": __version__,
            "implementation": governance["implementation"],
            "public_contract_version": governance["public_contract"]["version"],
        },
    )


@router.get("/service", response_model=ApiResponseEnvelope)
def info_service(runtime: MotorApiRuntime = Depends(get_runtime)) -> ApiResponseEnvelope:
    settings = runtime.config.integration_api()
    return ApiResponseEnvelope.service_message(
        status="ok",
        message="Estado del servicio API",
        success=True,
        result={
            **runtime.snapshot(),
            "service_name": runtime.config.service_name(),
            "environment": runtime.config.environment().value,
            "http_enabled": settings.http_enabled,
            "public_contract_version": settings.public_contract_version,
        },
    )


@router.get("/modules", response_model=ApiResponseEnvelope)
def info_modules(runtime: MotorApiRuntime = Depends(get_runtime)) -> ApiResponseEnvelope:
    modules = []
    for item in runtime.coordinator.get_pipeline_snapshot():
        modules.append(
            {
                "module_name": item.get("module_name"),
                "registered": item.get("registered"),
                "available": item.get("available"),
                "role": item.get("role"),
            },
        )
    return ApiResponseEnvelope.service_message(
        status="ok",
        message="Módulos registrados en el Coordinator",
        success=True,
        result={"modules": modules, "count": len(modules)},
    )
