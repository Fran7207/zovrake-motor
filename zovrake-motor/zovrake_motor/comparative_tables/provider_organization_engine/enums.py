"""Enumeraciones del Provider Organization Engine."""

from __future__ import annotations

from enum import Enum


class ProviderOrganizationBuildStatus(str, Enum):
    """Estado de la organización de proveedores."""

    ORGANIZED = "organized"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ProviderOrganizerStrategyType(str, Enum):
    """Estrategias de organización de proveedores."""

    GROUP_PROVIDER = "group_provider"
