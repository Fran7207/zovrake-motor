"""Modelos del Document Recognition Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType
from zovrake_motor.comprehension.recognition.enums import RecognitionConfidenceLevel, RecognitionStrategyType


@dataclass(frozen=True)
class DocumentRecognitionRequest:
    """Solicitud de reconocimiento documental — sin lectura de contenido."""

    process_id: UUID
    document_id: str
    file_name: str = ""
    mime_type: str | None = None
    format_type: str | None = None
    file_signature: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyRecognitionResult:
    """Resultado individual de una estrategia de reconocimiento."""

    strategy_type: RecognitionStrategyType
    strategy_name: str
    recognized: bool
    format_type: DocumentFormatType | None
    confidence: float
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_type": self.strategy_type.value,
            "strategy_name": self.strategy_name,
            "recognized": self.recognized,
            "format_type": self.format_type.value if self.format_type else None,
            "confidence": self.confidence,
            "technical_observations": list(self.technical_observations),
        }


@dataclass(frozen=True)
class AdapterSelectionPrepared:
    """Preparación de selección de adaptador — sin ejecutar el adaptador."""

    format_type: DocumentFormatType | None
    suggested_adapter: str | None
    adapter_resolvable: bool
    resolution_message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_type": self.format_type.value if self.format_type else None,
            "suggested_adapter": self.suggested_adapter,
            "adapter_resolvable": self.adapter_resolvable,
            "resolution_message": self.resolution_message,
        }


@dataclass(frozen=True)
class DocumentRecognitionResult:
    """Resultado estructurado y uniforme del reconocimiento documental."""

    process_id: UUID
    document_id: str
    recognized: bool
    identified_format: DocumentFormatType | None
    confidence: float
    confidence_level: RecognitionConfidenceLevel
    strategy_used: str | None
    strategy_type: RecognitionStrategyType | None
    suggested_adapter: str | None
    adapter_selection: AdapterSelectionPrepared | None
    technical_observations: tuple[str, ...]
    strategies_executed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "recognized": self.recognized,
            "identified_format": self.identified_format.value if self.identified_format else None,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "strategy_used": self.strategy_used,
            "strategy_type": self.strategy_type.value if self.strategy_type else None,
            "suggested_adapter": self.suggested_adapter,
            "adapter_selection": (
                self.adapter_selection.to_dict() if self.adapter_selection is not None else None
            ),
            "technical_observations": list(self.technical_observations),
            "strategies_executed": self.strategies_executed,
        }
