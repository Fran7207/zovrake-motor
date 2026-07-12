"""Contratos de entrega al ERP — inmutables, sin interpretación."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ecg.enums import EcgContractVersion


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AnalysisResultDeliveryReference:
    """Referencia al Resultado del Análisis Inteligente — sin modificación."""

    result_reference_id: str
    catalog_id: str = ""
    prepared: bool = True
    executed: bool = False
    source_data_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_reference_id": self.result_reference_id,
            "catalog_id": self.catalog_id,
            "prepared": self.prepared,
            "executed": self.executed,
            "source_data_preserved": self.source_data_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeTablesDeliveryReference:
    """Referencia a Cuadros Comparativos — sin modificación."""

    catalog_id: str = ""
    prepared: bool = True
    source_data_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "prepared": self.prepared,
            "source_data_preserved": self.source_data_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TraceabilityDeliveryBundle:
    """Trazabilidad entregada al ERP — inmutable."""

    process_id: str
    project_id: str
    quotation_id: str
    pipeline_transitions: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "pipeline_transitions": list(self.pipeline_transitions),
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ErpControlledError:
    """Error controlado entregado al ERP."""

    error_code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class ErpAnalysisDelivery:
    """
    Entrega oficial al Centro de Evidencias (ERP).

    Inmutable: no modifica recomendaciones, explicaciones, evidencias,
    confianza ni trazabilidad del Motor.
    """

    process_id: UUID
    project_id: str
    quotation_id: str
    success: bool
    message: str
    analysis_status: str
    immutable: bool = True
    analysis_result: AnalysisResultDeliveryReference | None = None
    comparative_tables: ComparativeTablesDeliveryReference | None = None
    traceability: TraceabilityDeliveryBundle | None = None
    controlled_error: ErpControlledError | None = None
    occurred_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)
    contract_version: str = EcgContractVersion.V1.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "project_id": self.project_id,
            "quotation_id": self.quotation_id,
            "success": self.success,
            "message": self.message,
            "analysis_status": self.analysis_status,
            "immutable": self.immutable,
            "analysis_result": (
                self.analysis_result.to_dict() if self.analysis_result is not None else None
            ),
            "comparative_tables": (
                self.comparative_tables.to_dict()
                if self.comparative_tables is not None
                else None
            ),
            "traceability": (
                self.traceability.to_dict() if self.traceability is not None else None
            ),
            "controlled_error": (
                self.controlled_error.to_dict()
                if self.controlled_error is not None
                else None
            ),
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": self.metadata,
            "contract_version": self.contract_version,
        }
