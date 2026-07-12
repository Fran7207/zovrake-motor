"""Group Integrity Engine — exportaciones públicas."""

from zovrake_motor.comparative_tables.group_integrity_engine.engine import GroupIntegrityEngineCore
from zovrake_motor.comparative_tables.group_integrity_engine.exceptions import (
    ColumnCatalogAccessError,
    ProviderCatalogAccessError,
    RowCatalogAccessError,
    StructureCatalogAccessError,
)
from zovrake_motor.comparative_tables.group_integrity_engine.gateway import (
    IntegrityValidationInputGateway,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityReport,
    GroupIntegrityValidationRequest,
    GroupIntegrityValidationResult,
)

__all__ = [
    "ColumnCatalogAccessError",
    "GroupIntegrityEngineCore",
    "GroupIntegrityReport",
    "GroupIntegrityValidationRequest",
    "GroupIntegrityValidationResult",
    "IntegrityValidationInputGateway",
    "ProviderCatalogAccessError",
    "RowCatalogAccessError",
    "StructureCatalogAccessError",
]
