"""Excepciones del Comparative Domain Model Builder."""


class ComparativeDomainModelBuildError(Exception):
    """Error base del CDMB."""


class ContextAssociationCatalogAccessError(ComparativeDomainModelBuildError):
    """Error al acceder al catálogo de asociaciones de contexto."""


class DomainModelBuilderNotFoundError(ComparativeDomainModelBuildError):
    """Constructor de modelo comparativo no registrado."""
