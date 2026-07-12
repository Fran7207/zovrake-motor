"""Context Integration Engine — Implementación 2.9."""

from zovrake_motor.comprehension.context_integration.association_builder import ContextAssociationBuilder
from zovrake_motor.comprehension.context_integration.classification_hook import ClassificationContextPoint
from zovrake_motor.comprehension.context_integration.context_builder import RequirementContextBuilder
from zovrake_motor.comprehension.context_integration.dki_hook import DkiAssociationPoint
from zovrake_motor.comprehension.context_integration.engine import ContextIntegrationEngine
from zovrake_motor.comprehension.context_integration.enums import ContextIncidentSeverity, ContextIntegrationStatus
from zovrake_motor.comprehension.context_integration.exceptions import (
    ContextInputError,
    ContextIntegrationError,
    DocumentModelImmutableError,
    DuplicateContextAssociationError,
    TraceabilityError,
)
from zovrake_motor.comprehension.context_integration.gateway import ContextInputGateway
from zovrake_motor.comprehension.context_integration.integration import ContextIntegrationMotorIntegration
from zovrake_motor.comprehension.context_integration.models import (
    ContextAssociation,
    ContextIntegrationRequest,
    ContextIntegrationResult,
    ContextTraceability,
    RequirementContextModel,
)
from zovrake_motor.comprehension.context_integration.reasoning_hook import ReasoningContextPoint
from zovrake_motor.comprehension.context_integration.store import ContextIntegrationStore

__all__ = [
    "ClassificationContextPoint",
    "ContextAssociation",
    "ContextAssociationBuilder",
    "ContextInputError",
    "ContextInputGateway",
    "ContextIntegrationEngine",
    "ContextIntegrationError",
    "ContextIntegrationMotorIntegration",
    "ContextIntegrationRequest",
    "ContextIntegrationResult",
    "ContextIntegrationStatus",
    "ContextIntegrationStore",
    "ContextIncidentSeverity",
    "ContextTraceability",
    "DkiAssociationPoint",
    "DocumentModelImmutableError",
    "DuplicateContextAssociationError",
    "ReasoningContextPoint",
    "RequirementContextBuilder",
    "RequirementContextModel",
    "TraceabilityError",
]
