"""Canonical Representation Engine — Implementación 2.6."""

from zovrake_motor.comprehension.canonical.assembler import CanonicalAssembler
from zovrake_motor.comprehension.canonical.classification_hook import ClassificationIntegrationPoint
from zovrake_motor.comprehension.canonical.engine import CanonicalRepresentationEngine
from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType, TransformationIncidentSeverity
from zovrake_motor.comprehension.canonical.exceptions import (
    CanonicalEngineError,
    ExtractionInputError,
    ImmutabilityViolationError,
    TraceabilityError,
    TransformerNotFoundError,
)
from zovrake_motor.comprehension.canonical.gateway import ExtractionResultGateway
from zovrake_motor.comprehension.canonical.integration import RepresentationMotorIntegration
from zovrake_motor.comprehension.canonical.models import (
    CanonicalCommercialInformation,
    CanonicalCondition,
    CanonicalDocument,
    CanonicalItem,
    CanonicalMetadata,
    CanonicalObservation,
    CanonicalProvider,
    CanonicalRepresentationRequest,
    CanonicalRepresentationResult,
    CanonicalTechnicalInformation,
    CanonicalTraceability,
    TransformationIncident,
)
from zovrake_motor.comprehension.canonical.port import CanonicalSectionTransformerPort
from zovrake_motor.comprehension.canonical.registry import TransformerRegistry
from zovrake_motor.comprehension.canonical.transformers import (
    CommercialInformationTransformer,
    ConditionsTransformer,
    ItemsTransformer,
    MetadataTransformer,
    ObservationsTransformer,
    ProviderTransformer,
    TechnicalInformationTransformer,
)

__all__ = [
    "CanonicalAssembler",
    "CanonicalCommercialInformation",
    "CanonicalCondition",
    "CanonicalDocument",
    "CanonicalEngineError",
    "CanonicalItem",
    "CanonicalMetadata",
    "CanonicalObservation",
    "CanonicalProvider",
    "CanonicalRepresentationEngine",
    "CanonicalRepresentationRequest",
    "CanonicalRepresentationResult",
    "CanonicalSectionTransformerPort",
    "CanonicalSectionType",
    "CanonicalTechnicalInformation",
    "CanonicalTraceability",
    "ClassificationIntegrationPoint",
    "CommercialInformationTransformer",
    "ConditionsTransformer",
    "ExtractionInputError",
    "ExtractionResultGateway",
    "ImmutabilityViolationError",
    "ItemsTransformer",
    "MetadataTransformer",
    "ObservationsTransformer",
    "ProviderTransformer",
    "RepresentationMotorIntegration",
    "TechnicalInformationTransformer",
    "TraceabilityError",
    "TransformationIncident",
    "TransformationIncidentSeverity",
    "TransformerNotFoundError",
    "TransformerRegistry",
]
