"""Estrategias de reconocimiento documental del DRE."""

from zovrake_motor.comprehension.recognition.strategies.extension import ExtensionRecognitionStrategy
from zovrake_motor.comprehension.recognition.strategies.magic_number import MagicNumberRecognitionStrategy
from zovrake_motor.comprehension.recognition.strategies.metadata import MetadataRecognitionStrategy
from zovrake_motor.comprehension.recognition.strategies.mime_type import MimeTypeRecognitionStrategy

__all__ = [
    "ExtensionRecognitionStrategy",
    "MagicNumberRecognitionStrategy",
    "MetadataRecognitionStrategy",
    "MimeTypeRecognitionStrategy",
]
