"""Rutas REST de análisis — gestión del ciclo de vida ERP ↔ Motor."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request

from zovrake_motor.api.bootstrap import MotorApiRuntime
from zovrake_motor.api.http.envelope import ApiResponseEnvelope
from zovrake_motor.api.http.schemas import AnalysisQueryParams, CreateAnalysisPayload

router = APIRouter(prefix="/analyses", tags=["analyses"])


def get_runtime(request: Request) -> MotorApiRuntime:
    return request.app.state.runtime


@router.post("", response_model=ApiResponseEnvelope, status_code=202)
def create_analysis(
    payload: CreateAnalysisPayload,
    background_tasks: BackgroundTasks,
    runtime: MotorApiRuntime = Depends(get_runtime),
) -> ApiResponseEnvelope:
    public_request = payload.to_public_request()
    response = runtime.integration_api.start_analysis(public_request)
    if response.success:
        background_tasks.add_task(runtime.integration_api.process_pending)
    envelope = ApiResponseEnvelope.from_public_response(response)
    return envelope


@router.get("/{analysis_id}", response_model=ApiResponseEnvelope)
def get_analysis(
    analysis_id: UUID,
    project_id: str = Query(default=""),
    quotation_id: str = Query(default=""),
    runtime: MotorApiRuntime = Depends(get_runtime),
) -> ApiResponseEnvelope:
    params = AnalysisQueryParams(project_id=project_id, quotation_id=quotation_id)
    status = runtime.integration_api.query_status(params.to_status_query(analysis_id))
    result = runtime.integration_api.query_result(params.to_result_query(analysis_id))
    envelope = ApiResponseEnvelope.from_public_response(status)
    if result.result is not None:
        envelope.result = result.result.to_dict()
    return envelope


@router.get("/{analysis_id}/status", response_model=ApiResponseEnvelope)
def get_analysis_status(
    analysis_id: UUID,
    project_id: str = Query(default=""),
    quotation_id: str = Query(default=""),
    runtime: MotorApiRuntime = Depends(get_runtime),
) -> ApiResponseEnvelope:
    params = AnalysisQueryParams(project_id=project_id, quotation_id=quotation_id)
    response = runtime.integration_api.query_status(params.to_status_query(analysis_id))
    return ApiResponseEnvelope.from_public_response(response)


@router.get("/{analysis_id}/result", response_model=ApiResponseEnvelope)
def get_analysis_result(
    analysis_id: UUID,
    project_id: str = Query(default=""),
    quotation_id: str = Query(default=""),
    result_reference_id: str = Query(default=""),
    runtime: MotorApiRuntime = Depends(get_runtime),
) -> ApiResponseEnvelope:
    params = AnalysisQueryParams(
        project_id=project_id,
        quotation_id=quotation_id,
        result_reference_id=result_reference_id,
    )
    response = runtime.integration_api.query_result(params.to_result_query(analysis_id))
    return ApiResponseEnvelope.from_public_response(response)
