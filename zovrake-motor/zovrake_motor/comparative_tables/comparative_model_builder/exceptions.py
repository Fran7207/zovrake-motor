"""Excepciones del Comparative Model Builder."""


class EnrichedCatalogAccessError(Exception):
    """Error de acceso al catálogo enriquecido del TME."""


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


class ModelBuilderNotFoundError(Exception):
    """Constructor de modelos no registrado en el CMB."""
