"""Contratos base de la API Interna."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ContractEnvelope:
    """Sobre común de todos los contratos — versionado obligatorio."""

    contract_version: str = ContractVersionRegistry.ACTIVE_VERSION
    contract_name: str = ContractVersionRegistry.CONTRACT_NAME

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "contract_name": self.contract_name,
        }


@dataclass(frozen=True)
class InternalApiRequestBase:
    """Base de solicitudes internas."""

    process_id: UUID
    codigo_req: str = ""
    contract_version: str = ContractVersionRegistry.ACTIVE_VERSION
    contract_name: str = ContractVersionRegistry.CONTRACT_NAME
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.base_dict()

    def base_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "codigo_req": self.codigo_req,
            "contract_version": self.contract_version,
            "contract_name": self.contract_name,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class InternalApiResponseBase:
    """Base de respuestas internas."""

    process_id: UUID
    success: bool
    message: str
    contract_version: str = ContractVersionRegistry.ACTIVE_VERSION
    contract_name: str = ContractVersionRegistry.CONTRACT_NAME
    occurred_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.base_dict()

    def base_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "success": self.success,
            "message": self.message,
            "contract_version": self.contract_version,
            "contract_name": self.contract_name,
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": self.metadata,
        }
