"""Registro en memoria de resultados de análisis ejecutados por el Motor."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from uuid import UUID


@dataclass
class StoredAnalysisResult:
    """Resultado real del Motor listo para entrega al ERP."""

    process_id: UUID
    codigo_req: str
    catalog_id: str
    executed: bool
    message: str
    comparative_tables: dict[str, Any]
    intelligent_analysis: dict[str, Any]
    documents_processed: tuple[dict[str, Any], ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_structured_metadata(self) -> dict[str, Any]:
        return {
            "query_prepared": True,
            "executed": self.executed,
            "codigo_req": self.codigo_req,
            "comparative_tables": self.comparative_tables,
            "intelligent_analysis": self.intelligent_analysis,
            "documents_processed": list(self.documents_processed),
            **self.metadata,
        }


class AnalysisResultRegistry:
    """Almacén de resultados por ``process_id`` — consultable por la API Interna."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._by_process: dict[UUID, StoredAnalysisResult] = {}

    def store(self, result: StoredAnalysisResult) -> None:
        with self._lock:
            self._by_process[result.process_id] = result

    def get(self, process_id: UUID) -> StoredAnalysisResult | None:
        with self._lock:
            return self._by_process.get(process_id)

    def has(self, process_id: UUID) -> bool:
        with self._lock:
            return process_id in self._by_process

    def clear(self) -> None:
        with self._lock:
            self._by_process.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._by_process)
