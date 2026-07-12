"""Contrato del Módulo de Generación de Cuadros Comparativos."""

from __future__ import annotations

from abc import ABC, abstractmethod

from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
    ComparativeStructureBuildResult,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeColumnBuildRequest,
    ComparativeColumnBuildResult,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildRequest,
    ComparativeRowBuildResult,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationBuildRequest,
    ProviderOrganizationBuildResult,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityValidationRequest,
    GroupIntegrityValidationResult,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    TraceabilityMetadataEnrichmentRequest,
    TraceabilityMetadataEnrichmentResult,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildRequest,
    ComparativeModelBuildResult,
)
from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationRequest,
    ComparativeModelValidationResult,
)
from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationRequest,
    ComparativeQualityValidationResult,
)
from zovrake_motor.comparative_tables.models import ComparativeTablesRequest, ComparativeTablesResult


class ComparativeTablesPort(ABC):
    """Punto de entrada del módulo de Generación de Cuadros Comparativos."""

    @abstractmethod
    def prepare(self, request: ComparativeTablesRequest) -> ComparativeTablesResult:
        """Preparará generación de cuadros comparativos — sin procesamiento en esta etapa."""

    @abstractmethod
    def build_comparative_structure(
        self,
        request: ComparativeStructureBuildRequest,
    ) -> ComparativeStructureBuildResult:
        """Construirá la estructura base de cada Cuadro Comparativo."""

    @abstractmethod
    def build_dynamic_columns(
        self,
        request: ComparativeColumnBuildRequest,
    ) -> ComparativeColumnBuildResult:
        """Construirá las columnas dinámicas de cada Cuadro Comparativo."""

    @abstractmethod
    def build_dynamic_rows(
        self,
        request: ComparativeRowBuildRequest,
    ) -> ComparativeRowBuildResult:
        """Construirá las filas dinámicas de cada Cuadro Comparativo."""

    @abstractmethod
    def organize_providers(
        self,
        request: ProviderOrganizationBuildRequest,
    ) -> ProviderOrganizationBuildResult:
        """Organizará los proveedores dentro de cada Cuadro Comparativo."""

    @abstractmethod
    def validate_group_integrity(
        self,
        request: GroupIntegrityValidationRequest,
    ) -> GroupIntegrityValidationResult:
        """Validará la integridad estructural de cada Cuadro Comparativo."""

    @abstractmethod
    def enrich_traceability_metadata(
        self,
        request: TraceabilityMetadataEnrichmentRequest,
    ) -> TraceabilityMetadataEnrichmentResult:
        """Enriquecerá cada Cuadro Comparativo con trazabilidad y metadatos."""

    @abstractmethod
    def build_comparative_model(
        self,
        request: ComparativeModelBuildRequest,
    ) -> ComparativeModelBuildResult:
        """Construirá el Modelo Comparativo Definitivo por cada Grupo Comparable."""

    @abstractmethod
    def validate_comparative_model(
        self,
        request: ComparativeModelValidationRequest,
    ) -> ComparativeModelValidationResult:
        """Validará el Modelo Comparativo Definitivo."""

    @abstractmethod
    def audit_comparative_quality(
        self,
        request: ComparativeQualityValidationRequest,
    ) -> ComparativeQualityValidationResult:
        """Auditará la calidad integral del módulo de cuadros comparativos."""
