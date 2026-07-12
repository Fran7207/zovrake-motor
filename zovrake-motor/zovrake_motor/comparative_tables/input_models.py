"""Referencias de entrada del Modelo Comparativo de Dominio — sin acoplamiento directo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ComparativeDomainModelReference:
    """
    Referencia al Modelo Comparativo de Dominio (PM5).

    El módulo de cuadros comparativos consume exclusivamente esta referencia;
    nunca accede a documentos originales ni modelos intermedios.
    """

    catalog_id: str
    model_id: str
    document_id: str
    process_id: str
    contract_version: str = "1.0"
    pm6_output_contract: bool = True
    source_data_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "model_id": self.model_id,
            "document_id": self.document_id,
            "process_id": self.process_id,
            "contract_version": self.contract_version,
            "pm6_output_contract": self.pm6_output_contract,
            "source_data_preserved": self.source_data_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ComparativeTablesInputBundle:
    """
    Paquete de entrada proveniente de Clasificación Inteligente.

    Contrato preparatorio para consumo exclusivo del Modelo Comparativo de Dominio.
    """

    process_id: UUID
    domain_model: ComparativeDomainModelReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "domain_model": (
                self.domain_model.to_dict() if self.domain_model is not None else None
            ),
        }
