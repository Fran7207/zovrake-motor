"""Contrato base de transformadores de sección del CRE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalCommercialInformation,
    CanonicalCondition,
    CanonicalItem,
    CanonicalMetadata,
    CanonicalObservation,
    CanonicalProvider,
    CanonicalTechnicalInformation,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class CanonicalSectionTransformerPort(ABC):
    """
    Contrato común para transformadores de sección del Modelo Canónico.

    Cada transformador tiene una única responsabilidad y no interpreta el contenido.
    """

    @property
    @abstractmethod
    def transformer_name(self) -> str:
        """Identificador único del transformador."""

    @property
    @abstractmethod
    def transformer_label(self) -> str:
        """Etiqueta descriptiva del transformador."""

    @property
    @abstractmethod
    def section_type(self) -> CanonicalSectionType:
        """Sección del Modelo Canónico que transforma."""

    @abstractmethod
    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        """Transforma una sección — sin interpretación en esta etapa."""

    def snapshot(self) -> dict[str, Any]:
        return {
            "transformer_name": self.transformer_name,
            "transformer_label": self.transformer_label,
            "section_type": self.section_type.value,
        }


class ProviderTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Proveedor."""

    @abstractmethod
    def build_provider(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalProvider:
        """Construye la sección Proveedor."""


class CommercialInformationTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Información Comercial."""

    @abstractmethod
    def build_commercial_information(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalCommercialInformation:
        """Construye la sección Información Comercial."""


class TechnicalInformationTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Información Técnica."""

    @abstractmethod
    def build_technical_information(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalTechnicalInformation:
        """Construye la sección Información Técnica."""


class ItemsTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Ítems."""

    @abstractmethod
    def build_items(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalItem, ...]:
        """Construye la sección Ítems."""


class ConditionsTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Condiciones."""

    @abstractmethod
    def build_conditions(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalCondition, ...]:
        """Construye la sección Condiciones."""


class ObservationsTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Observaciones."""

    @abstractmethod
    def build_observations(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalObservation, ...]:
        """Construye la sección Observaciones."""


class MetadataTransformerPort(CanonicalSectionTransformerPort):
    """Transformador de la sección Metadatos."""

    @abstractmethod
    def build_metadata(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> CanonicalMetadata:
        """Construye la sección Metadatos."""
