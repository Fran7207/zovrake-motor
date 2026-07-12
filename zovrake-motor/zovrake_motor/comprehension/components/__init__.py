"""Componentes internos del Módulo de Comprensión Documental."""

from zovrake_motor.comprehension.components.adapters import DocumentAdaptersManager
from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.components.context_manager import DocumentContextManager
from zovrake_motor.comprehension.components.document_coordinator import DocumentCoordinator
from zovrake_motor.comprehension.components.document_index import DocumentIndex
from zovrake_motor.comprehension.components.extractors import ExtractorsRegistry
from zovrake_motor.comprehension.components.format_identifier import FormatIdentifier
from zovrake_motor.comprehension.components.model_builder import InternalModelBuilder
from zovrake_motor.comprehension.components.normalizer import ContentNormalizer
from zovrake_motor.comprehension.components.quality_manager import DocumentQualityManager
from zovrake_motor.comprehension.components.traceability_manager import DocumentTraceabilityManager
from zovrake_motor.comprehension.components.validator import DocumentValidator

__all__ = [
    "ComprehensionComponentPort",
    "ContentNormalizer",
    "DocumentAdaptersManager",
    "DocumentContextManager",
    "DocumentCoordinator",
    "DocumentIndex",
    "DocumentQualityManager",
    "DocumentTraceabilityManager",
    "DocumentValidator",
    "ExtractorsRegistry",
    "FormatIdentifier",
    "InternalModelBuilder",
]
