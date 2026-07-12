"""Concept Analysis Engine (CAE) — exportaciones públicas."""

from zovrake_motor.classification.concept_analysis.catalog import (
    ConceptCatalogBuilder,
    TemporaryConceptCatalogStore,
)
from zovrake_motor.classification.concept_analysis.engine import ConceptAnalysisEngine
from zovrake_motor.classification.concept_analysis.enums import (
    ConceptAnalysisStatus,
    ConceptDetectorType,
    ConceptKind,
)
from zovrake_motor.classification.concept_analysis.exceptions import (
    ConceptAnalysisError,
    ConceptDetectorNotFoundError,
    InternalModelAccessError,
)
from zovrake_motor.classification.concept_analysis.gateway import InternalModelGateway, InternalModelView
from zovrake_motor.classification.concept_analysis.integration import ConceptAnalysisMotorIntegration
from zovrake_motor.classification.concept_analysis.integration_hooks import (
    ConceptNormalizationIntegrationPoint,
    MaterialClassificationIntegrationPoint,
    ServiceClassificationIntegrationPoint,
)
from zovrake_motor.classification.concept_analysis.models import (
    ConceptAnalysisIncident,
    ConceptAnalysisRequest,
    ConceptAnalysisResult,
    ConceptCandidate,
    ConceptCatalog,
    ConceptLocation,
    ConceptTraceability,
    DetectorResult,
)
from zovrake_motor.classification.concept_analysis.port import ConceptDetectorPort
from zovrake_motor.classification.concept_analysis.registry import ConceptDetectorRegistry

__all__ = [
    "ConceptAnalysisEngine",
    "ConceptAnalysisError",
    "ConceptAnalysisIncident",
    "ConceptAnalysisMotorIntegration",
    "ConceptAnalysisRequest",
    "ConceptAnalysisResult",
    "ConceptAnalysisStatus",
    "ConceptCandidate",
    "ConceptCatalog",
    "ConceptCatalogBuilder",
    "ConceptDetectorNotFoundError",
    "ConceptDetectorPort",
    "ConceptDetectorRegistry",
    "ConceptDetectorType",
    "ConceptKind",
    "ConceptLocation",
    "ConceptNormalizationIntegrationPoint",
    "ConceptTraceability",
    "DetectorResult",
    "InternalModelAccessError",
    "InternalModelGateway",
    "InternalModelView",
    "MaterialClassificationIntegrationPoint",
    "ServiceClassificationIntegrationPoint",
    "TemporaryConceptCatalogStore",
]
