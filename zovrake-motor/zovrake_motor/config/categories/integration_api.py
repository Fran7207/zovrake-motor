"""Configuración de la API de Integración Pública — fuente centralizada."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationApiSettings:
    """
    Configuración de la API de Integración Pública.

    HTTP, autenticación y autorización quedan preparados para 9.2+.
    """

    enabled: bool = True
    prepared: bool = True
    public_contract_version: str = "v1"
    http_enabled: bool = True
    http_transport_prepared: bool = True
    authentication_prepared: bool = True
    authorization_prepared: bool = True
    cors_prepared: bool = True
    health_endpoint_prepared: bool = True
    max_documents_per_request: int = 100
    max_concurrent_analyses: int = 1_000

    @classmethod
    def default(cls) -> IntegrationApiSettings:
        return cls()
