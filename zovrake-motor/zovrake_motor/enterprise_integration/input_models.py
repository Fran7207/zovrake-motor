"""Referencias de entrada del Resultado del Análisis Inteligente — sin acoplamiento directo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class IntelligentAnalysisResultReference:
    """
    Referencia al Resultado del Análisis Inteligente (PM7).

    El módulo de integración consume exclusivamente esta referencia;
    nunca accede a artefactos intermedios del Motor ni al Frontend del ERP.
    """

    catalog_id: str
    model_id: str
    document_id: str
    process_id: str
    contract_version: str = "1.0"
    pm7_output_contract_prepared: bool = True
    pm8_input_contract_prepared: bool = True
    source_data_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "model_id": self.model_id,
            "document_id": self.document_id,
            "process_id": self.process_id,
            "contract_version": self.contract_version,
            "pm7_output_contract_prepared": self.pm7_output_contract_prepared,
            "pm8_input_contract_prepared": self.pm8_input_contract_prepared,
            "source_data_preserved": self.source_data_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EnterpriseIntegrationInputBundle:
    """
    Paquete de entrada proveniente del Motor Inteligente (PM7).

    Contrato preparatorio para consumo exclusivo del Resultado del Análisis Inteligente.
    """

    process_id: UUID
    analysis_result: IntelligentAnalysisResultReference | None = None
    codigo_req: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "codigo_req": self.codigo_req,
            "analysis_result": (
                self.analysis_result.to_dict()
                if self.analysis_result is not None
                else None
            ),
        }
