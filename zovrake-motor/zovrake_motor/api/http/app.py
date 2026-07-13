"""Aplicación FastAPI oficial del Motor Inteligente ZOVRAKE."""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from zovrake_motor import __version__
from zovrake_motor.api.bootstrap import MotorApiRuntime, build_motor_api_runtime
from zovrake_motor.api.governance import PUBLIC_CONTRACT_VERSION, governance_snapshot
from zovrake_motor.api.http.envelope import ApiErrorBody, ApiResponseEnvelope, utc_now
from zovrake_motor.api.http.routes import analyses_router, health_router, info_router

logger = logging.getLogger("zovrake_motor.api.http")


def create_app(*, runtime: MotorApiRuntime | None = None) -> FastAPI:
    """
    Factory de la API REST oficial.

    Si no se provee runtime, inicializa Coordinator + IntegrationApiService.
    """
    app = FastAPI(
        title="ZOVRAKE Motor Inteligente — API Oficial",
        description=(
            "Puerta de entrada exclusiva entre el ERP y el Motor Inteligente. "
            "Toda solicitud se valida y delega al Coordinator vía Integración Empresarial."
        ),
        version=__version__,
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    if runtime is None:
        runtime = build_motor_api_runtime()
    app.state.runtime = runtime
    settings = runtime.config.integration_api()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router_prefix = "/api/v1"
    app.include_router(analyses_router, prefix=api_router_prefix)
    app.include_router(health_router, prefix=api_router_prefix)
    app.include_router(info_router, prefix=api_router_prefix)

    @app.get(f"{api_router_prefix}", response_model=ApiResponseEnvelope, tags=["service"])
    def api_root() -> ApiResponseEnvelope:
        governance = governance_snapshot()
        return ApiResponseEnvelope.service_message(
            status="ok",
            message="API oficial del Motor Inteligente ZOVRAKE",
            success=True,
            result={
                "motor_version": __version__,
                "implementation": governance["implementation"],
                "public_contract_version": PUBLIC_CONTRACT_VERSION,
                "http_enabled": settings.http_enabled,
            },
        )

    @app.middleware("http")
    async def log_request_lifecycle(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid4()))
        started_at = utc_now()
        logger.info(
            "api_request_started request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        response = await call_next(request)
        finished_at = utc_now()
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        logger.info(
            "api_request_finished request_id=%s status=%s duration_ms=%s",
            request_id,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-Id"] = request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details: dict[str, Any] = {"validation_errors": jsonable_encoder(exc.errors())}
        envelope = ApiResponseEnvelope.service_message(
            status="invalid_request",
            message="La solicitud no cumple el contrato público",
            success=False,
            error=ApiErrorBody(
                code="invalid_request",
                message="Estructura de solicitud inválida",
                recoverable=True,
                details=details,
            ),
        )
        return JSONResponse(status_code=422, content=envelope.model_dump(mode="json"))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        envelope = ApiResponseEnvelope.service_message(
            status="http_error",
            message=str(exc.detail),
            success=False,
            error=ApiErrorBody(
                code="http_error",
                message=str(exc.detail),
                recoverable=exc.status_code < 500,
                details={"status_code": exc.status_code},
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("api_internal_error path=%s", request.url.path)
        envelope = ApiResponseEnvelope.service_message(
            status="internal_error",
            message="Error interno del servicio API",
            success=False,
            error=ApiErrorBody(
                code="internal_error",
                message="Error interno del servicio API",
                recoverable=False,
                details={"error_type": type(exc).__name__},
            ),
        )
        return JSONResponse(status_code=500, content=envelope.model_dump(mode="json"))

    return app
