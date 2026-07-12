"""Traceability & Metadata Engine — exportaciones públicas."""

from zovrake_motor.comparative_tables.traceability_metadata_engine.engine import (
    TraceabilityMetadataEngineCore,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.exceptions import (
    ColumnCatalogAccessError,
    IntegrityReportAccessError,
    ProviderCatalogAccessError,
    RowCatalogAccessError,
    StructureCatalogAccessError,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.gateway import (
    MetadataEnrichmentInputGateway,
)
from zovrake_motor.comparative_tables.traceability_metadata_engine.models import (
    EnrichedComparativeTableCatalog,
    TraceabilityMetadataEnrichmentRequest,
    TraceabilityMetadataEnrichmentResult,
)

__all__ = [
    "ColumnCatalogAccessError",
    "EnrichedComparativeTableCatalog",
    "IntegrityReportAccessError",
    "MetadataEnrichmentInputGateway",
    "ProviderCatalogAccessError",
    "RowCatalogAccessError",
    "StructureCatalogAccessError",
    "TraceabilityMetadataEngineCore",
    "TraceabilityMetadataEnrichmentRequest",
    "TraceabilityMetadataEnrichmentResult",
]
