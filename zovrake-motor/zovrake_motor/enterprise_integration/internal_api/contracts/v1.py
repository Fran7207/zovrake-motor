"""Metadatos del contrato v1 de la API Interna."""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "v1"
CONTRACT_NAME = "InternalIntegrationApi"

REQUIRED_START_ANALYSIS_FIELDS: tuple[str, ...] = (
    "process_id",
    "codigo_req",
    "contract_version",
)

REQUIRED_STATUS_QUERY_FIELDS: tuple[str, ...] = (
    "process_id",
    "contract_version",
)

REQUIRED_RESULT_QUERY_FIELDS: tuple[str, ...] = (
    "process_id",
    "contract_version",
)

REQUIRED_CANCEL_FIELDS: tuple[str, ...] = (
    "process_id",
    "contract_version",
)

REQUIRED_VALIDATE_FIELDS: tuple[str, ...] = (
    "process_id",
    "contract_version",
    "target_operation",
)

REQUEST_CONTRACTS: tuple[dict[str, Any], ...] = (
    {
        "operation": "start_analysis",
        "version": CONTRACT_VERSION,
        "required_fields": list(REQUIRED_START_ANALYSIS_FIELDS),
    },
    {
        "operation": "query_status",
        "version": CONTRACT_VERSION,
        "required_fields": list(REQUIRED_STATUS_QUERY_FIELDS),
    },
    {
        "operation": "query_result",
        "version": CONTRACT_VERSION,
        "required_fields": list(REQUIRED_RESULT_QUERY_FIELDS),
    },
    {
        "operation": "cancel_analysis",
        "version": CONTRACT_VERSION,
        "required_fields": list(REQUIRED_CANCEL_FIELDS),
    },
    {
        "operation": "validate_request",
        "version": CONTRACT_VERSION,
        "required_fields": list(REQUIRED_VALIDATE_FIELDS),
    },
)

RESPONSE_CONTRACTS: tuple[dict[str, Any], ...] = (
    {
        "type": "start_analysis_response",
        "version": CONTRACT_VERSION,
        "required_fields": ("process_id", "success", "message", "occurred_at", "processing_status"),
    },
    {
        "type": "analysis_status_response",
        "version": CONTRACT_VERSION,
        "required_fields": ("process_id", "success", "message", "occurred_at", "processing_status"),
    },
    {
        "type": "analysis_result_response",
        "version": CONTRACT_VERSION,
        "required_fields": ("process_id", "success", "message", "occurred_at", "processing_status"),
    },
    {
        "type": "internal_api_error_response",
        "version": CONTRACT_VERSION,
        "required_fields": ("error_code", "message", "occurred_at"),
    },
)

def contract_snapshot() -> dict[str, Any]:
    return {
        "version": CONTRACT_VERSION,
        "name": CONTRACT_NAME,
        "request_contracts": list(REQUEST_CONTRACTS),
        "response_contracts": list(RESPONSE_CONTRACTS),
    }
