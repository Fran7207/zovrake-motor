"""Módulo de Clasificación Inteligente — Implementación 3.12 (Prompt Maestro 5 CERRADO)."""

from zovrake_motor.classification.comparable_group_builder import (
    ComparableGroupBuildRequest,
    ComparableGroupBuildResult,
    ComparableGroupBuilderEngine,
    ComparableGroupCatalog,
    ComparableGroupRecord,
)
from zovrake_motor.classification.comparative_domain_model import (
    ComparativeDomainModelBuildRequest,
    ComparativeDomainModelBuildResult,
    ComparativeDomainModelBuilderEngine,
    ComparativeDomainModelCatalog,
    ComparativeDomainModelRecord,
)
from zovrake_motor.classification.context_association import (
    ContextAssociationEngine,
    ContextAssociationRequest,
    ContextAssociationResult,
    ContextAssociationCatalog,
)
from zovrake_motor.classification.concept_analysis import (
    ConceptAnalysisEngine,
    ConceptAnalysisRequest,
    ConceptAnalysisResult,
    ConceptCandidate,
    ConceptCatalog,
    ConceptKind,
)
from zovrake_motor.classification.concept_normalization import (
    ConceptNormalizationEngine,
    ConceptNormalizationRequest,
    ConceptNormalizationResult,
    NormalizedConceptCatalog,
    NormalizedConceptRecord,
)
from zovrake_motor.classification.equivalence_detection import (
    EquivalenceCatalog,
    EquivalenceDetectionEngine,
    EquivalenceDetectionRequest,
    EquivalenceDetectionResult,
    EquivalenceRecord,
)
from zovrake_motor.classification.material_classification import (
    MaterialCatalog,
    MaterialClassificationEngine,
    MaterialClassificationRequest,
    MaterialClassificationResult,
    MaterialRecord,
)
from zovrake_motor.classification.service_classification import (
    ServiceCatalog,
    ServiceClassificationEngine,
    ServiceClassificationRequest,
    ServiceClassificationResult,
    ServiceRecord,
)
from zovrake_motor.classification.enums import ClassificationComponentType, ClassificationPhase
from zovrake_motor.classification.input_gateway import ComprehensionOutputGateway
from zovrake_motor.classification.input_models import (
    ClassificationInputBundle,
    DocumentIndexReference,
    IntegratedContextReference,
    InternalDocumentModelReference,
)
from zovrake_motor.classification.integration import ClassificationMotorIntegration
from zovrake_motor.classification.models import (
    ClassificationRequest,
    ClassificationResult,
    ComponentDescriptor,
)
from zovrake_motor.classification.pipeline import ClassificationPipeline
from zovrake_motor.classification.port import ClassificationPort
from zovrake_motor.classification.registry import ComponentRegistry
from zovrake_motor.classification.service import ClassificationService
from zovrake_motor.classification.classification_quality import (
    ClassificationQualityFrameworkEngine,
    ClassificationQualityReport,
    ClassificationQualityValidationRequest,
    ClassificationQualityValidationResult,
)

__all__ = [
    "ClassificationComponentType",
    "ClassificationInputBundle",
    "ClassificationMotorIntegration",
    "ClassificationPhase",
    "ClassificationPipeline",
    "ClassificationPort",
    "ClassificationQualityFrameworkEngine",
    "ClassificationQualityReport",
    "ClassificationQualityValidationRequest",
    "ClassificationQualityValidationResult",
    "ClassificationRequest",
    "ClassificationResult",
    "ClassificationService",
    "ComparableGroupBuildRequest",
    "ComparableGroupBuildResult",
    "ComparableGroupBuilderEngine",
    "ComparableGroupCatalog",
    "ComparableGroupRecord",
    "ComparativeDomainModelBuildRequest",
    "ComparativeDomainModelBuildResult",
    "ComparativeDomainModelBuilderEngine",
    "ComparativeDomainModelCatalog",
    "ComparativeDomainModelRecord",
    "ComponentDescriptor",
    "ComponentRegistry",
    "ComprehensionOutputGateway",
    "ConceptAnalysisEngine",
    "ConceptAnalysisRequest",
    "ConceptAnalysisResult",
    "ConceptCandidate",
    "ConceptCatalog",
    "ConceptKind",
    "ConceptNormalizationEngine",
    "ConceptNormalizationRequest",
    "ConceptNormalizationResult",
    "ContextAssociationCatalog",
    "ContextAssociationEngine",
    "ContextAssociationRequest",
    "ContextAssociationResult",
    "DocumentIndexReference",
    "EquivalenceCatalog",
    "EquivalenceDetectionEngine",
    "EquivalenceDetectionRequest",
    "EquivalenceDetectionResult",
    "EquivalenceRecord",
    "IntegratedContextReference",
    "InternalDocumentModelReference",
    "MaterialCatalog",
    "MaterialClassificationEngine",
    "MaterialClassificationRequest",
    "MaterialClassificationResult",
    "MaterialRecord",
    "NormalizedConceptCatalog",
    "NormalizedConceptRecord",
    "ServiceCatalog",
    "ServiceClassificationEngine",
    "ServiceClassificationRequest",
    "ServiceClassificationResult",
    "ServiceRecord",
]
