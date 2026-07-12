"""Excepciones del Context Association Engine."""


class ContextAssociationError(Exception):
    """Error base del CAE-Context."""


class ComparableGroupCatalogAccessError(ContextAssociationError):
    """Error al acceder al catálogo de grupos comparables."""


class IntegratedContextAccessError(ContextAssociationError):
    """Error al acceder al contexto integrado."""


class ContextAssociatorNotFoundError(ContextAssociationError):
    """Asociador de contexto no registrado."""
