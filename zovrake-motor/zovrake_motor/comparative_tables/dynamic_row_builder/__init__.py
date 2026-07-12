"""Dynamic Row Builder — exportaciones públicas."""

from zovrake_motor.comparative_tables.dynamic_row_builder.engine import DynamicRowBuilderEngine
from zovrake_motor.comparative_tables.dynamic_row_builder.exceptions import (
    ColumnCatalogAccessError,
    StructureCatalogAccessError,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import RowBuildInputGateway
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildRequest,
    ComparativeRowBuildResult,
    ComparativeTableRowCatalog,
    ComparativeTableRowDefinition,
)

__all__ = [
    "ColumnCatalogAccessError",
    "ComparativeRowBuildRequest",
    "ComparativeRowBuildResult",
    "ComparativeTableRowCatalog",
    "ComparativeTableRowDefinition",
    "DynamicRowBuilderEngine",
    "RowBuildInputGateway",
    "StructureCatalogAccessError",
]
