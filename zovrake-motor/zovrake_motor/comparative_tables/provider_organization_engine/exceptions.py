"""Excepciones del Provider Organization Engine."""


class StructureCatalogAccessError(Exception):
    """Error al acceder al catálogo de estructuras del CSE."""


class ColumnCatalogAccessError(Exception):
    """Error al acceder al catálogo de columnas del DCB."""


class RowCatalogAccessError(Exception):
    """Error al acceder al catálogo de filas del DRB."""


class ProviderOrganizerNotFoundError(Exception):
    """Organizador de proveedores no registrado."""
