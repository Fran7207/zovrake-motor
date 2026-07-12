"""Contrato base de enriquecedores del Traceability & Metadata Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comparative_tables.traceability_metadata_engine.enums import (
    MetadataEnricherStrategyType,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.gateway import (
    MetadataEnrichmentInputView,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import MetadataEnricherResult
from zovrake_motor.config.categories.comparative_tables import TraceabilityMetadataEngineSettings


class MetadataEnricherPort(ABC):
    """Contrato común para enriquecedores de trazabilidad y metadatos."""

    @property
    @abstractmethod
    def enricher_name(self) -> str:
        """Identificador único del enriquecedor."""

    @property
    @abstractmethod
    def enricher_label(self) -> str:
        """Etiqueta descriptiva del enriquecedor."""

    @property
    @abstractmethod
    def enricher_type(self) -> MetadataEnricherStrategyType:
        """Tipo de estrategia de enriquecimiento."""

    @abstractmethod
    def enrich(
        self,
        input_view: MetadataEnrichmentInputView,
        *,
        settings: TraceabilityMetadataEngineSettings,
        start_sequence: int,
    ) -> MetadataEnricherResult:
        """Enriquece trazabilidad y metadatos — sin modificar catálogos de entrada."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "enricher_name": self.enricher_name,
            "enricher_label": self.enricher_label,
            "enricher_type": self.enricher_type.value,
        }
