"""Excepciones del Comparable Group Builder."""


class ComparableGroupBuildError(Exception):
    """Error base del CGB."""


class EquivalenceCatalogAccessError(ComparableGroupBuildError):
    """Error al acceder al catálogo de equivalencias."""


class GroupBuilderNotFoundError(ComparableGroupBuildError):
    """Constructor de grupos no registrado."""
