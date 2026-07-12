"""Excepciones del Dynamic Column Builder."""


class StructureCatalogAccessError(Exception):
    """Error de acceso al catálogo de estructuras del CSE."""


class ColumnBuilderNotFoundError(Exception):
    """Constructor de columnas no registrado."""
