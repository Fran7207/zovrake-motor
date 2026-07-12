"""Enumeraciones del Document Knowledge Index."""

from __future__ import annotations

from enum import Enum


class IndexEntryStatus(str, Enum):
    """Estado de una entrada del índice documental."""

    REGISTERED = "registered"
    REUSE_PREPARED = "reuse_prepared"


class IndexingIncidentSeverity(str, Enum):
    """Severidad de incidencias durante la indexación."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
