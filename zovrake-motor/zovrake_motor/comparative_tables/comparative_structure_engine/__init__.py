"""Comparative Structure Engine — exportaciones públicas."""

from zovrake_motor.comparative_tables.comparative_structure_engine.engine import (
    ComparativeStructureBuilderEngine,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.exceptions import (
    DomainModelCatalogAccessError,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.gateway import (
    DomainModelCatalogGateway,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
    ComparativeStructureBuildResult,
    ComparativeTableBaseStructure,
    ComparativeTableStructureCatalog,
)

__all__ = [
    "ComparativeStructureBuildRequest",
    "ComparativeStructureBuildResult",
    "ComparativeStructureBuilderEngine",
    "ComparativeTableBaseStructure",
    "ComparativeTableStructureCatalog",
    "DomainModelCatalogAccessError",
    "DomainModelCatalogGateway",
]
