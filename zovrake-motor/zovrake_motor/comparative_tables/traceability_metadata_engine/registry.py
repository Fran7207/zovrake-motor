"""Registro centralizado de enriquecedores del TME."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.traceability_metadata_engine.enrichers_strategies import (
    ComparativeTableMetadataEnricher,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.exceptions import (
    MetadataEnricherNotFoundError,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.port import MetadataEnricherPort
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings


class MetadataEnricherRegistry:
    """Registro único de enriquecedores de trazabilidad y metadatos."""

    def __init__(self) -> None:
        self._enrichers_by_name: dict[str, MetadataEnricherPort] = {}
        self._enrichers_ordered: list[MetadataEnricherPort] = []

    def register(self, enricher: MetadataEnricherPort) -> None:
        if enricher.enricher_name in self._enrichers_by_name:
            raise ValueError(f"Enriquecedor ya registrado: {enricher.enricher_name}")
        self._enrichers_by_name[enricher.enricher_name] = enricher
        self._enrichers_ordered.append(enricher)

    def register_defaults(
        self,
        *,
        settings: TraceabilityMetadataEngineSettings | None = None,
    ) -> None:
        settings = settings or TraceabilityMetadataEngineSettings.default()
        candidates: list[tuple[bool, MetadataEnricherPort]] = [
            (
                settings.comparative_table_metadata_enricher_enabled,
                ComparativeTableMetadataEnricher(),
            ),
        ]
        for enabled, enricher in candidates:
            if enabled:
                self.register(enricher)

    def get(self, name: str) -> MetadataEnricherPort | None:
        return self._enrichers_by_name.get(name)

    def require(self, name: str) -> MetadataEnricherPort:
        enricher = self.get(name)
        if enricher is None:
            raise MetadataEnricherNotFoundError(f"Enriquecedor no registrado: {name}")
        return enricher

    def all_enrichers(self) -> tuple[MetadataEnricherPort, ...]:
        return tuple(self._enrichers_ordered)

    def count(self) -> int:
        return len(self._enrichers_ordered)

    def snapshot(self) -> list[dict[str, Any]]:
        return [enricher.snapshot() for enricher in self._enrichers_ordered]
