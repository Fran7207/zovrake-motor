"""Gateway de consumo de salidas de Comprensión Documental — sin acoplamiento directo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.input_models import ClassificationInputBundle
from zovrake_motor.config.categories.classification import ClassificationSettings


class ComprehensionOutputGateway:
    """
    Puente preparatorio para consumir IDMB, DKI y Contexto Integrado.

    No accede a documentos originales ni importa el módulo de Comprensión Documental.
    """

    def __init__(self, *, settings: ClassificationSettings | None = None) -> None:
        self._settings = settings or ClassificationSettings.default()

    @property
    def is_prepared(self) -> bool:
        return self._settings.comprehension_integration_prepared

    @property
    def is_enabled(self) -> bool:
        return self._settings.comprehension_enabled

    def can_consume(self) -> bool:
        return self.is_prepared and self.is_enabled

    def validate_input_bundle(self, bundle: ClassificationInputBundle) -> dict[str, Any]:
        """Validación estructural del paquete de entrada — sin procesamiento."""
        has_model = bundle.internal_model is not None
        has_index = bundle.index_reference is not None
        has_context = bundle.context_reference is not None

        return {
            "valid": self.is_prepared,
            "executed": False,
            "message": "Consumo preparado — sin ejecución en esta etapa",
            "process_id": str(bundle.process_id),
            "comprehension_integration_prepared": self.is_prepared,
            "comprehension_enabled": self.is_enabled,
            "internal_model_present": has_model,
            "index_reference_present": has_index,
            "context_reference_present": has_context,
            "accesses_original_documents": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }

    def prepare_consumption(self, bundle: ClassificationInputBundle) -> dict[str, Any]:
        """Prepara el consumo futuro de salidas de Comprensión Documental."""
        validation = self.validate_input_bundle(bundle)
        return {
            **validation,
            "consumption_ready": self.is_prepared,
            "classification_will_execute": False,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "comprehension_integration_prepared": self.is_prepared,
            "comprehension_enabled": self.is_enabled,
            "can_consume": self.can_consume(),
            "accesses_original_documents": False,
            "status": "prepared" if self.is_prepared else "not_prepared",
        }
