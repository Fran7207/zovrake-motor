"""Excepciones del Traceability & Metadata Engine."""


class StructureCatalogAccessError(Exception):
    """Error de acceso al catálogo de estructuras."""


class ColumnCatalogAccessError(Exception):
    """Error de acceso al catálogo de columnas."""


class RowCatalogAccessError(Exception):
    """Error de acceso al catálogo de filas."""


class ProviderCatalogAccessError(Exception):
    """Error de acceso al catálogo de proveedores."""


class IntegrityReportAccessError(Exception):
    """Error de acceso al reporte de integridad del GIE."""


class MetadataEnricherNotFoundError(Exception):
    """Enriquecedor no registrado en el registro del TME."""
