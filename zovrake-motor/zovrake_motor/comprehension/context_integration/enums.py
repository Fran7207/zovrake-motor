"""Enumeraciones del Context Integration Engine."""

from __future__ import annotations

from enum import Enum


class ContextIntegrationStatus(str, Enum):
    """Estado de una asociación de contexto integrada."""

    INTEGRATED = "integrated"
    PREPARED = "prepared"


class ContextIncidentSeverity(str, Enum):
    """Severidad de incidencias durante la integración de contexto."""

    INFO = "info"
    WARNING = "warning"
