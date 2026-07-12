"""Framework central de Validación Documental (DVF)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.validation.executor import ValidationExecutor
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, DocumentValidationResult
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.registry import ValidationRuleRegistry
from zovrake_motor.config.categories.comprehension import DocumentValidationSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentValidationFramework:
    """
    Document Validation Framework (DVF).

    Coordina todas las validaciones documentales del Motor Inteligente.
    El resto del Motor nunca valida documentos directamente.
    """

    EXPECTED_RULE_COUNT = 8

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ValidationRuleRegistry | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ValidationRuleRegistry()
        self._executor: ValidationExecutor | None = None
        self._initialized = False

    @property
    def registry(self) -> ValidationRuleRegistry:
        return self._registry

    @property
    def executor(self) -> ValidationExecutor:
        if self._executor is None:
            self._executor = ValidationExecutor(self._registry)
        return self._executor

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_RULE_COUNT

    def initialize(self) -> None:
        if not self._registry.count():
            self._registry.register_defaults(settings=self._validation_settings())
        self._executor = ValidationExecutor(self._registry)
        self._initialized = True

    def validate(self, request: DocumentValidationRequest) -> DocumentValidationResult:
        return self.executor.execute(request)

    def extend(self, rule: ValidationRulePort) -> None:
        """Incorpora una nueva regla mediante extensión sin modificar el núcleo."""
        self._registry.register(rule)

    def _validation_settings(self) -> DocumentValidationSettings:
        if self._config_provider is not None:
            return self._config_provider.comprehension().validation
        return DocumentValidationSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._validation_settings()
        return {
            "initialized": self._initialized,
            "rules_count": self._registry.count(),
            "rules": self._registry.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "strict_mode": settings.strict_mode,
                "max_file_size_bytes": settings.max_file_size_bytes,
                "min_file_size_bytes": settings.min_file_size_bytes,
                "supported_formats": list(settings.supported_formats),
            },
        }
