"""
Capa de API de Integración Pública — Prompt Maestro 9.

Arquitectura definitiva ERP ↔ API ↔ Motor Inteligente.
Implementación 9.2 — Diseño arquitectónico + transporte HTTP REST.
"""

from zovrake_motor.api.enums import (
    IntegrationApiErrorCode,
    IntegrationApiLifecycleStage,
    IntegrationApiOperation,
    PublicContractVersion,
)
from zovrake_motor.api.governance import governance_snapshot
from zovrake_motor.api.models import (
    AnalysisDocumentReference,
    AnalysisStatusPayload,
    ControlledErrorPayload,
    PublicAnalysisRequest,
    PublicAnalysisResponse,
    PublicResultQuery,
    PublicStatusQuery,
    RequirementContext,
    StructuredAnalysisResultPayload,
)
from zovrake_motor.api.service import IntegrationApiService

__all__ = [
    "AnalysisDocumentReference",
    "AnalysisStatusPayload",
    "ControlledErrorPayload",
    "IntegrationApiErrorCode",
    "IntegrationApiLifecycleStage",
    "IntegrationApiOperation",
    "IntegrationApiService",
    "PublicAnalysisRequest",
    "PublicAnalysisResponse",
    "PublicContractVersion",
    "PublicResultQuery",
    "PublicStatusQuery",
    "RequirementContext",
    "StructuredAnalysisResultPayload",
    "governance_snapshot",
]
