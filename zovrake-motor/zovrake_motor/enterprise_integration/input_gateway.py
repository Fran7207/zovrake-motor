"""Gateway de consumo del Resultado del Análisis Inteligente — sin acoplamiento directo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.config.categories.enterprise_integration import EnterpriseIntegrationSettings
from zovrake_motor.enterprise_integration.input_models import EnterpriseIntegrationInputBundle


class IntelligentAnalysisOutputGateway:
    """
    Puente preparatorio para consumir el Resultado del Análisis Inteligente (PM7).

    No accede a artefactos intermedios del Motor ni importa el módulo
    de Razonamiento Inteligente.
    """

    def __init__(self, *, settings: EnterpriseIntegrationSettings | None = None) -> None:
        self._settings = settings or EnterpriseIntegrationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.intelligent_analysis_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.intelligent_analysis_enabled

    @property
    def pm8_input_contract_required(self) -> bool:
        return self._settings.pm8_input_contract_required

    def can_consume(self) -> bool:
        return self.is_prepared and self.is_enabled

    def validate_input_bundle(self, bundle: EnterpriseIntegrationInputBundle) -> dict[str, Any]:
        """Validación estructural del paquete de entrada — sin procesamiento."""
        has_analysis_result = bundle.analysis_result is not None
        contract_valid = (
            bundle.analysis_result.pm7_output_contract_prepared is True
            and bundle.analysis_result.pm8_input_contract_prepared is True
            and bundle.analysis_result.source_data_preserved is True
            if bundle.analysis_result is not None
            else False
        )

        return {
            "valid": self.is_prepared,
            "executed": False,
            "message": "Consumo preparado — sin ejecución en esta etapa",
            "process_id": str(bundle.process_id),
            "intelligent_analysis_integration_prepared": self.is_prepared,
            "intelligent_analysis_enabled": self.is_enabled,
            "analysis_result_present": has_analysis_result,
            "pm7_output_contract_valid": (
                bundle.analysis_result.pm7_output_contract_prepared is True
                if bundle.analysis_result is not None
                else False
            ),
            "pm8_input_contract_valid": contract_valid,
            "pm8_input_contract_required": self.pm8_input_contract_required,
            "accesses_intelligent_analysis_internals": False,
            "accesses_erp_frontend": False,
            "accesses_intermediate_catalogs": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_consumption(self, bundle: EnterpriseIntegrationInputBundle) -> dict[str, Any]:
        """Prepara el consumo futuro del Resultado del Análisis Inteligente."""
        validation = self.validate_input_bundle(bundle)
        return {
            **validation,
            "consumption_ready": self.is_prepared,
            "enterprise_integration_will_execute": False,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "intelligent_analysis_integration_prepared": self.is_prepared,
            "intelligent_analysis_enabled": self.is_enabled,
            "pm8_input_contract_required": self.pm8_input_contract_required,
            "can_consume": self.can_consume(),
            "accesses_intelligent_analysis_internals": False,
            "accesses_erp_frontend": False,
            "accesses_intermediate_catalogs": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
