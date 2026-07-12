"""Contratos del ERP Communication Gateway."""

from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import (
    AnalysisResultDeliveryReference,
    ComparativeTablesDeliveryReference,
    ErpAnalysisDelivery,
    ErpControlledError,
    TraceabilityDeliveryBundle,
)
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.ecg.contracts.v1 import contract_snapshot

__all__ = [
    "AnalysisResultDeliveryReference",
    "ComparativeTablesDeliveryReference",
    "ErpAnalysisDelivery",
    "ErpControlledError",
    "EvidenceCenterAnalysisRequest",
    "EvidenceCenterResultQuery",
    "EvidenceCenterStatusQuery",
    "EvidenceDocumentReference",
    "RequirementDetailsReference",
    "TraceabilityDeliveryBundle",
    "contract_snapshot",
]
