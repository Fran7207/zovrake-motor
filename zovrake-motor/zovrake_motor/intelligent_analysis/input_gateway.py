"""Gateway de consumo del Modelo Comparativo Definitivo — sin acoplamiento directo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.config.categories.intelligent_analysis import IntelligentAnalysisSettings
from zovrake_motor.intelligent_analysis.input_models import IntelligentAnalysisInputBundle


class ComparativeTablesOutputGateway:
    """
    Puente preparatorio para consumir el Modelo Comparativo Definitivo (PM6).

    No accede a documentos originales, modelos intermedios ni importa
    el módulo de Generación de Cuadros Comparativos.
    """

    def __init__(self, *, settings: IntelligentAnalysisSettings | None = None) -> None:
        self._settings = settings or IntelligentAnalysisSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comparative_tables_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.comparative_tables_enabled

    @property
    def pm7_input_contract_required(self) -> bool:
        return self._settings.pm7_input_contract_required

    def can_consume(self) -> bool:
        return self.is_prepared and self.is_enabled

    def validate_input_bundle(self, bundle: IntelligentAnalysisInputBundle) -> dict[str, Any]:
        """Validación estructural del paquete de entrada — sin procesamiento."""
        has_definitive_model = bundle.definitive_model is not None
        contract_valid = (
            bundle.definitive_model.pm6_definitive_output_contract is True
            and bundle.definitive_model.pm7_input_contract_prepared is True
            if bundle.definitive_model is not None
            else False
        )

        return {
            "valid": self.is_prepared,
            "executed": False,
            "message": "Consumo preparado — sin ejecución en esta etapa",
            "process_id": str(bundle.process_id),
            "comparative_tables_integration_prepared": self.is_prepared,
            "comparative_tables_enabled": self.is_enabled,
            "definitive_model_present": has_definitive_model,
            "pm6_definitive_output_contract_valid": (
                bundle.definitive_model.pm6_definitive_output_contract is True
                if bundle.definitive_model is not None
                else False
            ),
            "pm7_input_contract_valid": contract_valid,
            "pm7_input_contract_required": self.pm7_input_contract_required,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "accesses_comparable_groups": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_consumption(self, bundle: IntelligentAnalysisInputBundle) -> dict[str, Any]:
        """Prepara el consumo futuro del Modelo Comparativo Definitivo."""
        validation = self.validate_input_bundle(bundle)
        return {
            **validation,
            "consumption_ready": self.is_prepared,
            "intelligent_analysis_will_execute": False,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "comparative_tables_integration_prepared": self.is_prepared,
            "comparative_tables_enabled": self.is_enabled,
            "pm7_input_contract_required": self.pm7_input_contract_required,
            "can_consume": self.can_consume(),
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "accesses_comparable_groups": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
