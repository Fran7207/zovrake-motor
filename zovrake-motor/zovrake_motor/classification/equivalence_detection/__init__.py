"""Equivalence Detection Engine (EDE) — exportaciones públicas."""

from zovrake_motor.classification.equivalence_detection.catalog import EquivalenceCatalogStore
from zovrake_motor.classification.equivalence_detection.engine import EquivalenceDetectionEngine
from zovrake_motor.classification.equivalence_detection.enums import (
    EquivalenceDetectionStatus,
    EquivalenceDetectorType,
    EquivalenceRelationType,
    EvidenceLevel,
)
from zovrake_motor.classification.equivalence_detection.exceptions import (
    EquivalenceDetectionError,
    EquivalenceDetectorNotFoundError,
    NormalizedCatalogAccessError,
)
from zovrake_motor.classification.equivalence_detection.gateway import (
    NormalizedConceptCatalogGateway,
    NormalizedConceptCatalogView,
)
from zovrake_motor.classification.equivalence_detection.integration import (
    EquivalenceDetectionMotorIntegration,
)
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceCatalog,
    EquivalenceDetectionIncident,
    EquivalenceDetectionRequest,
    EquivalenceDetectionResult,
    EquivalenceExplainability,
    EquivalenceRecord,
    EquivalenceTraceability,
)
from zovrake_motor.classification.equivalence_detection.port import EquivalenceDetectorPort
from zovrake_motor.classification.equivalence_detection.registry import EquivalenceDetectorRegistry

__all__ = [
    "EquivalenceCatalog",
    "EquivalenceCatalogStore",
    "EquivalenceDetectionEngine",
    "EquivalenceDetectionError",
    "EquivalenceDetectionIncident",
    "EquivalenceDetectionMotorIntegration",
    "EquivalenceDetectionRequest",
    "EquivalenceDetectionResult",
    "EquivalenceDetectionStatus",
    "EquivalenceDetectorNotFoundError",
    "EquivalenceDetectorPort",
    "EquivalenceDetectorRegistry",
    "EquivalenceDetectorType",
    "EquivalenceExplainability",
    "EquivalenceRecord",
    "EquivalenceRelationType",
    "EquivalenceTraceability",
    "EvidenceLevel",
    "NormalizedCatalogAccessError",
    "NormalizedConceptCatalogGateway",
    "NormalizedConceptCatalogView",
]
