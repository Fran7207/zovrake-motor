"""Registro centralizado de políticas de reintento."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.ftrrf.enums import (
    ErrorCategory,
    RetryStrategy,
)
from zovrake_motor.enterprise_integration.ftrrf.models import RetryPolicy


class RetryPolicyRegistry:
    """
    Resuelve la política de reintento aplicable a cada categoría de error.

    Solo los errores recuperables admiten reintentos.
    """

    def __init__(
        self,
        *,
        default_max_retries: int = 3,
        default_interval_seconds: float = 0.0,
    ) -> None:
        self._default_max_retries = default_max_retries
        self._default_interval_seconds = default_interval_seconds
        self._policies: dict[ErrorCategory, RetryPolicy] = self._build_defaults()

    def _build_defaults(self) -> dict[ErrorCategory, RetryPolicy]:
        recoverable = {
            ErrorCategory.COMMUNICATION,
            ErrorCategory.PROCESSING,
            ErrorCategory.TEMPORARY,
        }
        policies: dict[ErrorCategory, RetryPolicy] = {}
        for category in ErrorCategory:
            is_recoverable = category in recoverable
            policies[category] = RetryPolicy(
                category=category,
                recoverable=is_recoverable,
                max_retries=self._default_max_retries if is_recoverable else 0,
                interval_seconds=self._default_interval_seconds if is_recoverable else 0.0,
                strategy=(
                    RetryStrategy.FIXED_INTERVAL if is_recoverable else RetryStrategy.NONE
                ),
                cancel_on_categories=(
                    ErrorCategory.VALIDATION,
                    ErrorCategory.DOCUMENTAL,
                    ErrorCategory.PERMANENT,
                ),
            )
        return policies

    def register(self, policy: RetryPolicy) -> None:
        self._policies[policy.category] = policy

    def policy_for(self, category: ErrorCategory) -> RetryPolicy:
        return self._policies[category]

    def snapshot(self) -> list[dict]:
        return [policy.to_dict() for policy in self._policies.values()]
