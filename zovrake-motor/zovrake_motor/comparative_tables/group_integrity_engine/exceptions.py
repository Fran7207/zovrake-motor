"""Excepciones del Group Integrity Engine."""


class StructureCatalogAccessError(Exception):
    """Error al acceder al catálogo de estructuras del CSE."""


class ColumnCatalogAccessError(Exception):
    """Error al acceder al catálogo de columnas del DCB."""


class RowCatalogAccessError(Exception):
    """Error al acceder al catálogo de filas del DRB."""


class ProviderCatalogAccessError(Exception):
    """Error al acceder al catálogo de proveedores del POE."""


class IntegrityValidatorNotFoundError(Exception):
    """Validador de integridad no registrado."""
