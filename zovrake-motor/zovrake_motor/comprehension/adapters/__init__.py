"""Document Adapter Framework — Implementación 2.2."""

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.adapters.exceptions import (
    AdapterFrameworkError,
    AdapterNotFoundError,
    AdapterResolutionError,
)
from zovrake_motor.comprehension.adapters.framework import DocumentAdapterFramework
from zovrake_motor.comprehension.adapters.implementations import (
    ExcelDocumentAdapter,
    ImageDocumentAdapter,
    PdfDocumentAdapter,
    WordDocumentAdapter,
)
from zovrake_motor.comprehension.adapters.models import (
    AdapterDescriptor,
    AdapterResolutionRequest,
    AdapterResolutionResult,
)
from zovrake_motor.comprehension.adapters.port import DocumentAdapterPort
from zovrake_motor.comprehension.adapters.registry import AdapterRegistry
from zovrake_motor.comprehension.adapters.resolver import AdapterResolver

__all__ = [
    "AdapterDescriptor",
    "AdapterFrameworkError",
    "AdapterNotFoundError",
    "AdapterRegistry",
    "AdapterResolutionError",
    "AdapterResolutionRequest",
    "AdapterResolutionResult",
    "AdapterResolver",
    "DocumentAdapterFramework",
    "DocumentAdapterPort",
    "DocumentFormatType",
    "ExcelDocumentAdapter",
    "ImageDocumentAdapter",
    "PdfDocumentAdapter",
    "WordDocumentAdapter",
]
