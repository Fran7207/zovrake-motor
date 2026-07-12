"""Contrato del Módulo de Comprensión Documental."""

from __future__ import annotations

from abc import ABC, abstractmethod

from zovrake_motor.comprehension.models import ComprehensionRequest, ComprehensionResult
from zovrake_motor.comprehension.knowledge_index.models import DocumentIndexRequest, DocumentIndexResult
from zovrake_motor.comprehension.context_integration.models import ContextIntegrationRequest, ContextIntegrationResult
from zovrake_motor.comprehension.internal_model.models import InternalModelBuildRequest, InternalModelBuildResult
from zovrake_motor.comprehension.canonical.models import CanonicalRepresentationRequest, CanonicalRepresentationResult
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ContentExtractionResult
from zovrake_motor.comprehension.recognition.models import DocumentRecognitionRequest, DocumentRecognitionResult
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, DocumentValidationResult


class ComprehensionPort(ABC):
    """Punto de entrada del módulo de Comprensión Documental."""

    @abstractmethod
    def prepare(self, request: ComprehensionRequest) -> ComprehensionResult:
        """Preparará comprensión documental — sin procesamiento en esta etapa."""

    @abstractmethod
    def validate_document(self, request: DocumentValidationRequest) -> DocumentValidationResult:
        """Validará un documento antes de continuar en el Pipeline documental."""

    @abstractmethod
    def recognize_document(self, request: DocumentRecognitionRequest) -> DocumentRecognitionResult:
        """Identificará el tipo documental y preparará la selección del adaptador."""

    @abstractmethod
    def extract_content(self, request: ContentExtractionRequest) -> ContentExtractionResult:
        """Extraerá el contenido estructural del documento sin interpretación."""

    @abstractmethod
    def build_canonical_representation(
        self,
        request: CanonicalRepresentationRequest,
    ) -> CanonicalRepresentationResult:
        """Transformará la información extraída en Representación Canónica uniforme."""

    @abstractmethod
    def build_internal_model(self, request: InternalModelBuildRequest) -> InternalModelBuildResult:
        """Construirá el Modelo Documental Interno a partir de la Representación Canónica."""

    @abstractmethod
    def index_document(self, request: DocumentIndexRequest) -> DocumentIndexResult:
        """Indexará el Modelo Documental Interno en el índice de conocimiento documental."""

    @abstractmethod
    def integrate_context(self, request: ContextIntegrationRequest) -> ContextIntegrationResult:
        """Integrará el contexto del requerimiento con el Modelo Documental Interno indexado."""
