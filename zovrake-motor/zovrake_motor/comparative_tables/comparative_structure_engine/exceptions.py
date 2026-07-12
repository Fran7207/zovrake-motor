"""Excepciones del Comparative Structure Engine."""


class DomainModelCatalogAccessError(Exception):
    """Error de acceso al catálogo del Modelo Comparativo de Dominio."""


class StructureBuilderNotFoundError(Exception):
    """Constructor de estructuras no registrado."""
