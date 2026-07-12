"""Comparative Model Builder — exportaciones públicas."""

from zovrake_motor.comparative_tables.comparative_model_builder.engine import (
    ComparativeModelBuilderEngine,
)
from zovrake_motor.comparative_tables.comparative_model_builder.exceptions import (
    ColumnCatalogAccessError,
    EnrichedCatalogAccessError,
    IntegrityReportAccessError,
    ProviderCatalogAccessError,
    RowCatalogAccessError,
    StructureCatalogAccessError,
)
from zovrake_motor.comparative_tables.comparative_model_builder.gateway import (
    ModelBuildInputGateway,
)
from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME,
    PM6_DEFINITIVE_OUTPUT_CONTRACT_VERSION,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildRequest,
    ComparativeModelBuildResult,
    DefinitiveComparativeModel,
    DefinitiveComparativeModelCatalog,
)

__all__ = [
    "ColumnCatalogAccessError",
    "ComparativeModelBuildRequest",
    "ComparativeModelBuildResult",
    "ComparativeModelBuilderEngine",
    "DefinitiveComparativeModel",
    "DefinitiveComparativeModelCatalog",
    "EnrichedCatalogAccessError",
    "IntegrityReportAccessError",
    "ModelBuildInputGateway",
    "PM6_DEFINITIVE_OUTPUT_CONTRACT_NAME",
    "PM6_DEFINITIVE_OUTPUT_CONTRACT_VERSION",
    "ProviderCatalogAccessError",
    "RowCatalogAccessError",
    "StructureCatalogAccessError",
]
