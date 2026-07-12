"""Concept Normalization Engine (CNE) — exportaciones públicas."""

from zovrake_motor.classification.concept_normalization.catalog import NormalizedConceptCatalogStore
from zovrake_motor.classification.concept_normalization.engine import ConceptNormalizationEngine
from zovrake_motor.classification.concept_normalization.enums import (
    ConceptNormalizationStatus,
    ConceptNormalizerType,
    NormalizedConceptCategory,
)
from zovrake_motor.classification.concept_normalization.exceptions import (
    ClassificationCatalogAccessError,
    ConceptNormalizationError,
    ConceptNormalizerNotFoundError,
)
from zovrake_motor.classification.concept_normalization.gateway import (
    ClassificationCatalogGateway,
    ClassificationCatalogView,
)
from zovrake_motor.classification.concept_normalization.integration import (
    ConceptNormalizationMotorIntegration,
)
from zovrake_motor.classification.concept_normalization.models import (
    ConceptNormalizationIncident,
    ConceptNormalizationRequest,
    ConceptNormalizationResult,
    NormalizedConceptCatalog,
    NormalizedConceptRecord,
    NormalizedConceptTraceability,
    NormalizedModelReference,
)
from zovrake_motor.classification.concept_normalization.port import ConceptNormalizerPort
from zovrake_motor.classification.concept_normalization.registry import ConceptNormalizerRegistry

__all__ = [
    "ClassificationCatalogAccessError",
    "ClassificationCatalogGateway",
    "ClassificationCatalogView",
    "ConceptNormalizationEngine",
    "ConceptNormalizationError",
    "ConceptNormalizationIncident",
    "ConceptNormalizationMotorIntegration",
    "ConceptNormalizationRequest",
    "ConceptNormalizationResult",
    "ConceptNormalizationStatus",
    "ConceptNormalizerNotFoundError",
    "ConceptNormalizerPort",
    "ConceptNormalizerRegistry",
    "ConceptNormalizerType",
    "NormalizedConceptCatalog",
    "NormalizedConceptCatalogStore",
    "NormalizedConceptCategory",
    "NormalizedConceptRecord",
    "NormalizedConceptTraceability",
    "NormalizedModelReference",
]
