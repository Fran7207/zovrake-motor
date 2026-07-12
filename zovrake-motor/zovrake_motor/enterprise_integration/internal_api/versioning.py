"""Registro de versionado de contratos de la API Interna."""

from __future__ import annotations

from typing import Any

from zovrake_motor.enterprise_integration.internal_api.enums import ContractVersionId


class ContractVersionRegistry:
    """
    Registro de versiones de contrato — Contract First Design.

    Solo v1 está activa; v2 queda preparada para evolución sin ruptura.
    """

    ACTIVE_VERSION: str = ContractVersionId.V1.value
    SUPPORTED_VERSIONS: tuple[str, ...] = (ContractVersionId.V1.value,)
    FUTURE_VERSIONS: tuple[str, ...] = (ContractVersionId.V2.value,)

    CONTRACT_NAME = "InternalIntegrationApi"

    @classmethod
    def is_supported(cls, version: str) -> bool:
        return version in cls.SUPPORTED_VERSIONS

    @classmethod
    def is_future(cls, version: str) -> bool:
        return version in cls.FUTURE_VERSIONS

    @classmethod
    def normalize_version(cls, version: str) -> str:
        return version.strip().lower()

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        return {
            "contract_name": cls.CONTRACT_NAME,
            "active_version": cls.ACTIVE_VERSION,
            "supported_versions": list(cls.SUPPORTED_VERSIONS),
            "future_versions": list(cls.FUTURE_VERSIONS),
        }
