"""Fault Tolerance, Retry & Recovery Framework — Implementación 8.6."""

from zovrake_motor.enterprise_integration.ftrrf.classifier import ErrorClassifier
from zovrake_motor.enterprise_integration.ftrrf.enums import (
    ErrorCategory,
    ErrorSeverity,
    RecoveryDecision,
    RecoveryStage,
    RecoveryStatus,
    RetryStrategy,
)
from zovrake_motor.enterprise_integration.ftrrf.framework import (
    FaultToleranceRetryRecoveryFramework,
)
from zovrake_motor.enterprise_integration.ftrrf.models import (
    ErrorRecord,
    FaultClassification,
    RecoveryOutcome,
    RetryPolicy,
)
from zovrake_motor.enterprise_integration.ftrrf.retry_policy import RetryPolicyRegistry

__all__ = [
    "ErrorCategory",
    "ErrorClassifier",
    "ErrorRecord",
    "ErrorSeverity",
    "FaultClassification",
    "FaultToleranceRetryRecoveryFramework",
    "RecoveryDecision",
    "RecoveryOutcome",
    "RecoveryStage",
    "RecoveryStatus",
    "RetryPolicy",
    "RetryPolicyRegistry",
    "RetryStrategy",
]
