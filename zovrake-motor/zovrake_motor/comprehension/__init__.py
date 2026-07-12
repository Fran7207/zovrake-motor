"""Módulo de Comprensión Documental — Implementación 2.10 CERTIFICADO (Prompt Maestro 4)."""

from zovrake_motor.comprehension.adapters import (
    AdapterRegistry,
    DocumentAdapterFramework,
    DocumentAdapterPort,
    DocumentFormatType,
    ExcelDocumentAdapter,
    ImageDocumentAdapter,
    PdfDocumentAdapter,
    WordDocumentAdapter,
)
from zovrake_motor.comprehension.canonical import (
    CanonicalDocument,
    CanonicalRepresentationEngine,
    CanonicalRepresentationRequest,
    CanonicalRepresentationResult,
    CanonicalSectionTransformerPort,
    CanonicalTraceability,
    TransformerRegistry,
)
from zovrake_motor.comprehension.enums import ComprehensionComponentType, ComprehensionPhase
from zovrake_motor.comprehension.extraction import (
    AdapterDocumentContext,
    ContentExtractionEngine,
    ContentExtractionRequest,
    ContentExtractionResult,
    ContentExtractorPort,
    ExtractorRegistry,
    ExtractorType,
)
from zovrake_motor.comprehension.internal_model import (
    EntityBuilderRegistry,
    InternalDocumentModel,
    InternalDocumentModelBuilder,
    InternalEntityBuilderPort,
    InternalModelBuildRequest,
    InternalModelBuildResult,
    InternalTraceability,
)
from zovrake_motor.comprehension.knowledge_index import (
    DocumentIndexEntry,
    DocumentIndexRequest,
    DocumentIndexResult,
    DocumentIndexTraceability,
    DocumentKnowledgeIndex,
    IndexEntryStatus,
)
from zovrake_motor.comprehension.context_integration import (
    ContextAssociation,
    ContextIntegrationEngine,
    ContextIntegrationRequest,
    ContextIntegrationResult,
    ContextIntegrationStatus,
    RequirementContextModel,
)
from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
from zovrake_motor.comprehension.models import (
    ComponentDescriptor,
    ComprehensionRequest,
    ComprehensionResult,
)
from zovrake_motor.comprehension.pipeline import DocumentComprehensionPipeline
from zovrake_motor.comprehension.port import ComprehensionPort
from zovrake_motor.comprehension.recognition import (
    DocumentRecognitionEngine,
    DocumentRecognitionRequest,
    DocumentRecognitionResult,
    FormatCatalog,
    RecognitionStrategyPort,
    RecognitionStrategyRegistry,
)
from zovrake_motor.comprehension.registry import ComponentRegistry
from zovrake_motor.comprehension.service import ComprehensionService
from zovrake_motor.comprehension.validation import (
    DocumentValidationFramework,
    DocumentValidationRequest,
    DocumentValidationResult,
    ValidationStatus,
)

__all__ = [
    "AdapterDocumentContext",
    "AdapterRegistry",
    "CanonicalDocument",
    "CanonicalRepresentationEngine",
    "CanonicalRepresentationRequest",
    "CanonicalRepresentationResult",
    "CanonicalSectionTransformerPort",
    "CanonicalTraceability",
    "ComponentDescriptor",
    "ComprehensionComponentType",
    "ComprehensionMotorIntegration",
    "ComprehensionPhase",
    "ComprehensionPort",
    "ComprehensionRequest",
    "ComprehensionResult",
    "ComprehensionService",
    "ComponentRegistry",
    "ContentExtractionEngine",
    "ContextAssociation",
    "ContextIntegrationEngine",
    "ContextIntegrationRequest",
    "ContextIntegrationResult",
    "ContextIntegrationStatus",
    "ContentExtractionRequest",
    "ContentExtractionResult",
    "ContentExtractorPort",
    "DocumentAdapterFramework",
    "DocumentAdapterPort",
    "DocumentComprehensionPipeline",
    "DocumentFormatType",
    "DocumentIndexEntry",
    "DocumentIndexRequest",
    "DocumentIndexResult",
    "DocumentIndexTraceability",
    "DocumentKnowledgeIndex",
    "DocumentRecognitionEngine",
    "DocumentRecognitionRequest",
    "DocumentRecognitionResult",
    "DocumentValidationFramework",
    "DocumentValidationRequest",
    "DocumentValidationResult",
    "EntityBuilderRegistry",
    "ExcelDocumentAdapter",
    "ExtractorRegistry",
    "ExtractorType",
    "FormatCatalog",
    "ImageDocumentAdapter",
    "IndexEntryStatus",
    "InternalDocumentModel",
    "InternalDocumentModelBuilder",
    "InternalEntityBuilderPort",
    "InternalModelBuildRequest",
    "InternalModelBuildResult",
    "InternalTraceability",
    "PdfDocumentAdapter",
    "RecognitionStrategyPort",
    "RecognitionStrategyRegistry",
    "RequirementContextModel",
    "TransformerRegistry",
    "ValidationStatus",
    "WordDocumentAdapter",
]
