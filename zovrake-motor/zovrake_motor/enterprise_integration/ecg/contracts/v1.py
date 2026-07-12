"""Metadatos del contrato ECG v1."""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "v1"
CONTRACT_NAME = "ErpCommunicationGateway"
ERP_ENTRY_POINT = "EvidenceCenterAnalysisRequest"
ERP_DELIVERY_CONTRACT = "ErpAnalysisDelivery"

ERP_REQUEST_FIELDS: tuple[str, ...] = (
    "process_id",
    "project_id",
    "quotation_id",
    "requirement",
    "evidence_documents",
    "analysis_metadata",
    "contract_version",
)

ERP_DELIVERY_FIELDS: tuple[str, ...] = (
    "process_id",
    "project_id",
    "quotation_id",
    "success",
    "message",
    "analysis_status",
    "immutable",
    "occurred_at",
    "contract_version",
)


def contract_snapshot() -> dict[str, Any]:
    return {
        "version": CONTRACT_VERSION,
        "name": CONTRACT_NAME,
        "erp_entry_point": ERP_ENTRY_POINT,
        "erp_delivery_contract": ERP_DELIVERY_CONTRACT,
        "erp_request_fields": list(ERP_REQUEST_FIELDS),
        "erp_delivery_fields": list(ERP_DELIVERY_FIELDS),
        "immutability_enforced": True,
    }
