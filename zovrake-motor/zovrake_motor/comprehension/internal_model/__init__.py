"""Internal Document Model Builder — Implementación 2.7."""

from zovrake_motor.comprehension.internal_model.assembler import InternalModelAssembler
from zovrake_motor.comprehension.internal_model.classification_hook import ClassificationIntegrationPoint
from zovrake_motor.comprehension.internal_model.engine import InternalDocumentModelBuilder
from zovrake_motor.comprehension.internal_model.enums import InternalEntityType, ModelBuildIncidentSeverity
from zovrake_motor.comprehension.internal_model.exceptions import (
    CanonicalInputError,
    EntityBuilderNotFoundError,
    ImmutabilityViolationError,
    InternalModelBuilderError,
    TraceabilityError,
)
from zovrake_motor.comprehension.internal_model.gateway import CanonicalRepresentationGateway
from zovrake_motor.comprehension.internal_model.integration import InternalModelMotorIntegration
from zovrake_motor.comprehension.internal_model.models import (
    InternalCommercialConditionEntity,
    InternalCommercialInformationEntity,
    InternalDocumentEntity,
    InternalDocumentModel,
    InternalItemEntity,
    InternalMetadataEntity,
    InternalModelBuildRequest,
    InternalModelBuildResult,
    InternalObservationEntity,
    InternalOriginalReferencesEntity,
    InternalProviderEntity,
    InternalRequirementContextEntity,
    InternalTechnicalInformationEntity,
    InternalTraceability,
)
from zovrake_motor.comprehension.internal_model.port import InternalEntityBuilderPort
from zovrake_motor.comprehension.internal_model.registry import EntityBuilderRegistry

__all__ = [
    "CanonicalInputError",
    "CanonicalRepresentationGateway",
    "ClassificationIntegrationPoint",
    "EntityBuilderNotFoundError",
    "EntityBuilderRegistry",
    "ImmutabilityViolationError",
    "InternalCommercialConditionEntity",
    "InternalCommercialInformationEntity",
    "InternalDocumentEntity",
    "InternalDocumentModel",
    "InternalDocumentModelBuilder",
    "InternalEntityBuilderPort",
    "InternalEntityType",
    "InternalItemEntity",
    "InternalMetadataEntity",
    "InternalModelAssembler",
    "InternalModelBuildRequest",
    "InternalModelBuildResult",
    "InternalModelBuilderError",
    "InternalModelMotorIntegration",
    "InternalObservationEntity",
    "InternalOriginalReferencesEntity",
    "InternalProviderEntity",
    "InternalRequirementContextEntity",
    "InternalTechnicalInformationEntity",
    "InternalTraceability",
    "ModelBuildIncidentSeverity",
    "TraceabilityError",
]
