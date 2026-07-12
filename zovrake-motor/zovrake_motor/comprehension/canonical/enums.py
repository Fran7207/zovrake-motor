"""Enumeraciones del Canonical Representation Engine."""

from __future__ import annotations

from enum import Enum


class CanonicalSectionType(str, Enum):
    """Secciones del Modelo Canónico."""

    DOCUMENT = "document"
    PROVIDER = "provider"
    COMMERCIAL_INFORMATION = "commercial_information"
    TECHNICAL_INFORMATION = "technical_information"
    ITEMS = "items"
    CONDITIONS = "conditions"
    OBSERVATIONS = "observations"
    METADATA = "metadata"


class TransformationIncidentSeverity(str, Enum):
    """Severidad de incidencias durante la transformación canónica."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
