"""Content Extraction Engine — Implementación 2.5."""

from zovrake_motor.comprehension.extraction.adapter_gateway import AdapterDocumentGateway
from zovrake_motor.comprehension.extraction.engine import ContentExtractionEngine
from zovrake_motor.comprehension.extraction.enums import ExtractionIncidentSeverity, ExtractorType
from zovrake_motor.comprehension.extraction.exceptions import (
    AdapterAccessError,
    ExtractionEngineError,
    ExtractorNotFoundError,
    OriginalDocumentModifiedError,
)
from zovrake_motor.comprehension.extraction.executor import ExtractionExecutor
from zovrake_motor.comprehension.extraction.extractors import (
    EmbeddedImagesExtractor,
    FootersExtractor,
    HeadersExtractor,
    ListsExtractor,
    MetadataExtractor,
    StructuralElementsExtractor,
    TablesExtractor,
    TextExtractor,
)
from zovrake_motor.comprehension.extraction.integration import ExtractionMotorIntegration
from zovrake_motor.comprehension.extraction.models import (
    AdapterDocumentContext,
    ContentExtractionRequest,
    ContentExtractionResult,
    ExtractedTable,
    ExtractionIncident,
    ExtractorResult,
    StructuralElement,
)
from zovrake_motor.comprehension.extraction.ocr_hook import OcrIntegrationPoint
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort
from zovrake_motor.comprehension.extraction.registry import ExtractorRegistry

__all__ = [
    "AdapterAccessError",
    "AdapterDocumentContext",
    "AdapterDocumentGateway",
    "ContentExtractionEngine",
    "ContentExtractionRequest",
    "ContentExtractionResult",
    "ContentExtractorPort",
    "EmbeddedImagesExtractor",
    "ExtractedTable",
    "ExtractionEngineError",
    "ExtractionExecutor",
    "ExtractionIncident",
    "ExtractionIncidentSeverity",
    "ExtractionMotorIntegration",
    "ExtractorNotFoundError",
    "ExtractorRegistry",
    "ExtractorResult",
    "ExtractorType",
    "FootersExtractor",
    "HeadersExtractor",
    "ListsExtractor",
    "MetadataExtractor",
    "OcrIntegrationPoint",
    "OriginalDocumentModifiedError",
    "StructuralElement",
    "StructuralElementsExtractor",
    "TablesExtractor",
    "TextExtractor",
]
