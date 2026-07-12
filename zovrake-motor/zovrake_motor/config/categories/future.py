"""Configuraciones futuras del Motor Inteligente — estructura extensible."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OcrSettings:
    """OCR — reservado para implementaciones posteriores."""

    enabled: bool = False


@dataclass(frozen=True)
class AiSettings:
    """Modelos de IA — reservado para implementaciones posteriores."""

    enabled: bool = False
    default_model: str = ""


@dataclass(frozen=True)
class ApiSettings:
    """API REST — reservado para implementaciones posteriores."""

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass(frozen=True)
class StorageSettings:
    """Almacenamiento persistente — reservado para implementaciones posteriores."""

    enabled: bool = False
    backend: str = "local"


@dataclass(frozen=True)
class MonitoringSettings:
    """Monitoreo operativo — reservado para implementaciones posteriores."""

    enabled: bool = False


@dataclass(frozen=True)
class FutureSettings:
    """Agrupa configuraciones planificadas sin activar funcionalidades."""

    ocr: OcrSettings = field(default_factory=OcrSettings)
    ai: AiSettings = field(default_factory=AiSettings)
    api: ApiSettings = field(default_factory=ApiSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    monitoring: MonitoringSettings = field(default_factory=MonitoringSettings)

    @classmethod
    def default(cls) -> FutureSettings:
        return cls()
