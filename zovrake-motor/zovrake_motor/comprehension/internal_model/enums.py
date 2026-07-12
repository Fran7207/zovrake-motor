"""Enumeraciones del Internal Document Model Builder."""

from __future__ import annotations

from enum import Enum


class InternalEntityType(str, Enum):
    """Entidades del Modelo Documental Interno."""

    DOCUMENT = "document"
    PROVIDER = "provider"
    COMMERCIAL_INFORMATION = "commercial_information"
    TECHNICAL_INFORMATION = "technical_information"
    ITEMS = "items"
    COMMERCIAL_CONDITIONS = "commercial_conditions"
    OBSERVATIONS = "observations"
    METADATA = "metadata"
    REQUIREMENT_CONTEXT = "requirement_context"
    ORIGINAL_REFERENCES = "original_references"


class ModelBuildIncidentSeverity(str, Enum):
    """Severidad de incidencias durante la construcción del modelo."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
