"""Gateway de consumo del Modelo Comparativo de Dominio — sin acoplamiento directo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.input_models import ComparativeTablesInputBundle
from zovrake_motor.config.categories.comparative_tables import ComparativeTablesSettings


class ClassificationOutputGateway:
    """
    Puente preparatorio para consumir el Modelo Comparativo de Dominio (PM5).

    No accede a documentos originales, modelos intermedios ni importa
    el módulo de Clasificación Inteligente.
    """

    def __init__(self, *, settings: ComparativeTablesSettings | None = None) -> None:
        self._settings = settings or ComparativeTablesSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.classification_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.classification_enabled

    @property
    def pm6_output_contract_required(self) -> bool:
        return self._settings.pm6_output_contract_required

    def can_consume(self) -> bool:
        return self.is_prepared and self.is_enabled

    def validate_input_bundle(self, bundle: ComparativeTablesInputBundle) -> dict[str, Any]:
        """Validación estructural del paquete de entrada — sin procesamiento."""
        has_domain_model = bundle.domain_model is not None
        contract_valid = (
            bundle.domain_model.pm6_output_contract is True
            if bundle.domain_model is not None
            else False
        )

        return {
            "valid": self.is_prepared,
            "executed": False,
            "message": "Consumo preparado — sin ejecución en esta etapa",
            "process_id": str(bundle.process_id),
            "classification_integration_prepared": self.is_prepared,
            "classification_enabled": self.is_enabled,
            "domain_model_present": has_domain_model,
            "pm6_output_contract_valid": contract_valid,
            "pm6_output_contract_required": self.pm6_output_contract_required,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_consumption(self, bundle: ComparativeTablesInputBundle) -> dict[str, Any]:
        """Prepara el consumo futuro del Modelo Comparativo de Dominio."""
        validation = self.validate_input_bundle(bundle)
        return {
            **validation,
            "consumption_ready": self.is_prepared,
            "comparative_tables_will_execute": False,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "classification_integration_prepared": self.is_prepared,
            "classification_enabled": self.is_enabled,
            "pm6_output_contract_required": self.pm6_output_contract_required,
            "can_consume": self.can_consume(),
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
