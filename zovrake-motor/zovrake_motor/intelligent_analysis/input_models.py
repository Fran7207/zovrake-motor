"""Referencias de entrada del Modelo Comparativo Definitivo — sin acoplamiento directo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class DefinitiveComparativeModelReference:
    """
    Referencia al Modelo Comparativo Definitivo (PM6).

    El módulo de razonamiento consume exclusivamente esta referencia;
    nunca accede a documentos originales, modelos intermedios ni grupos comparables.
    """

    catalog_id: str
    model_id: str
    document_id: str
    process_id: str
    contract_version: str = "1.0"
    pm6_definitive_output_contract: bool = True
    pm7_input_contract_prepared: bool = True
    source_data_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "model_id": self.model_id,
            "document_id": self.document_id,
            "process_id": self.process_id,
            "contract_version": self.contract_version,
            "pm6_definitive_output_contract": self.pm6_definitive_output_contract,
            "pm7_input_contract_prepared": self.pm7_input_contract_prepared,
            "source_data_preserved": self.source_data_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class IntelligentAnalysisInputBundle:
    """
    Paquete de entrada proveniente de Generación de Cuadros Comparativos.

    Contrato preparatorio para consumo exclusivo del Modelo Comparativo Definitivo.
    """

    process_id: UUID
    definitive_model: DefinitiveComparativeModelReference | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "definitive_model": (
                self.definitive_model.to_dict()
                if self.definitive_model is not None
                else None
            ),
        }
