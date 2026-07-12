"""Excepciones del Context Integration Engine."""


class ContextIntegrationError(Exception):
    """Error base del Context Integration Engine."""


class ContextInputError(ContextIntegrationError):
    """Entrada de contexto inválida o de fuente no autorizada."""


class TraceabilityError(ContextIntegrationError):
    """Error en la cadena de trazabilidad del contexto."""


class DocumentModelImmutableError(ContextIntegrationError):
    """El modelo documental no puede modificarse durante la integración."""


class DuplicateContextAssociationError(ContextIntegrationError):
    """Asociación de contexto duplicada para el mismo documento y proceso."""
