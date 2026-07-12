"""Document Recognition Engine — Implementación 2.4."""

from zovrake_motor.comprehension.recognition.catalog import FormatCatalog
from zovrake_motor.comprehension.recognition.engine import DocumentRecognitionEngine
from zovrake_motor.comprehension.recognition.enums import RecognitionConfidenceLevel, RecognitionStrategyType
from zovrake_motor.comprehension.recognition.exceptions import (
    RecognitionEngineError,
    RecognitionExecutionError,
    RecognitionStrategyNotFoundError,
)
from zovrake_motor.comprehension.recognition.integration import RecognitionMotorIntegration
from zovrake_motor.comprehension.recognition.models import (
    AdapterSelectionPrepared,
    DocumentRecognitionRequest,
    DocumentRecognitionResult,
    StrategyRecognitionResult,
)
from zovrake_motor.comprehension.recognition.port import RecognitionStrategyPort
from zovrake_motor.comprehension.recognition.registry import RecognitionStrategyRegistry
from zovrake_motor.comprehension.recognition.resolver import RecognitionResolver
from zovrake_motor.comprehension.recognition.strategies import (
    ExtensionRecognitionStrategy,
    MagicNumberRecognitionStrategy,
    MetadataRecognitionStrategy,
    MimeTypeRecognitionStrategy,
)

__all__ = [
    "AdapterSelectionPrepared",
    "DocumentRecognitionEngine",
    "DocumentRecognitionRequest",
    "DocumentRecognitionResult",
    "ExtensionRecognitionStrategy",
    "FormatCatalog",
    "MagicNumberRecognitionStrategy",
    "MetadataRecognitionStrategy",
    "MimeTypeRecognitionStrategy",
    "RecognitionConfidenceLevel",
    "RecognitionEngineError",
    "RecognitionExecutionError",
    "RecognitionMotorIntegration",
    "RecognitionResolver",
    "RecognitionStrategyNotFoundError",
    "RecognitionStrategyPort",
    "RecognitionStrategyRegistry",
    "RecognitionStrategyType",
    "StrategyRecognitionResult",
]
