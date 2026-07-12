"""Contrato del Módulo de Clasificación Inteligente."""

from __future__ import annotations

from abc import ABC, abstractmethod

from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisRequest, ConceptAnalysisResult
from zovrake_motor.classification.material_classification.models import (
    MaterialClassificationRequest,
    MaterialClassificationResult,
)
from zovrake_motor.classification.service_classification.models import (
    ServiceClassificationRequest,
    ServiceClassificationResult,
)
from zovrake_motor.classification.concept_normalization.models import (
    ConceptNormalizationRequest,
    ConceptNormalizationResult,
)
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceDetectionRequest,
    EquivalenceDetectionResult,
)
from zovrake_motor.classification.comparable_group_builder.models import (
    ComparableGroupBuildRequest,
    ComparableGroupBuildResult,
)
from zovrake_motor.classification.context_association.models import (
    ContextAssociationRequest,
    ContextAssociationResult,
)
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildRequest,
    ComparativeDomainModelBuildResult,
)
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityValidationRequest,
    ClassificationQualityValidationResult,
)
from zovrake_motor.classification.models import ClassificationRequest, ClassificationResult


class ClassificationPort(ABC):
    """Punto de entrada del módulo de Clasificación Inteligente."""

    @abstractmethod
    def prepare(self, request: ClassificationRequest) -> ClassificationResult:
        """Preparará clasificación inteligente — sin procesamiento en esta etapa."""

    @abstractmethod
    def analyze_concepts(self, request: ConceptAnalysisRequest) -> ConceptAnalysisResult:
        """Identificará conceptos candidatos del Modelo Documental Interno."""

    @abstractmethod
    def classify_materials(self, request: MaterialClassificationRequest) -> MaterialClassificationResult:
        """Clasificará conceptos del CAE como materiales."""

    @abstractmethod
    def classify_services(self, request: ServiceClassificationRequest) -> ServiceClassificationResult:
        """Clasificará conceptos del CAE como servicios."""

    @abstractmethod
    def normalize_concepts(self, request: ConceptNormalizationRequest) -> ConceptNormalizationResult:
        """Normalizará la representación de materiales y servicios clasificados."""

    @abstractmethod
    def detect_equivalences(self, request: EquivalenceDetectionRequest) -> EquivalenceDetectionResult:
        """Detectará equivalencias entre conceptos normalizados."""

    @abstractmethod
    def build_comparable_groups(
        self,
        request: ComparableGroupBuildRequest,
    ) -> ComparableGroupBuildResult:
        """Construirá Grupos Comparables a partir del Modelo de Equivalencias."""

    @abstractmethod
    def associate_context(self, request: ContextAssociationRequest) -> ContextAssociationResult:
        """Asociará el contexto del requerimiento con cada Grupo Comparable."""

    @abstractmethod
    def build_comparative_domain_model(
        self,
        request: ComparativeDomainModelBuildRequest,
    ) -> ComparativeDomainModelBuildResult:
        """Construirá el Modelo Comparativo de Dominio — contrato oficial del PM5."""

    @abstractmethod
    def validate_classification_quality(
        self,
        request: ClassificationQualityValidationRequest,
    ) -> ClassificationQualityValidationResult:
        """Validará la calidad, consistencia e integridad de la clasificación."""
