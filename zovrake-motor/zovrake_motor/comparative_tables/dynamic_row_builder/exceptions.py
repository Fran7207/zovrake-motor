"""Excepciones del Dynamic Row Builder."""


class ColumnCatalogAccessError(Exception):
    """Error al acceder al catálogo de columnas del DCB."""


class StructureCatalogAccessError(Exception):
    """Error al acceder al catálogo de estructuras del CSE."""


class RowBuilderNotFoundError(Exception):
    """Constructor de filas no registrado."""
