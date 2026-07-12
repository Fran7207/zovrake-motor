"""Enumeraciones del Traceability & Metadata Engine."""

from __future__ import annotations

from enum import Enum


class TraceabilityMetadataEnrichmentStatus(str, Enum):
    """Estado del enriquecimiento de trazabilidad y metadatos."""

    ENRICHED = "enriched"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class MetadataEnricherStrategyType(str, Enum):
    """Tipos de estrategia de enriquecimiento."""

    COMPARATIVE_TABLE = "comparative_table"
