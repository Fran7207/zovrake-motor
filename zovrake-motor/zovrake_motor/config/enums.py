"""Enumeraciones del sistema de configuración centralizada."""

from __future__ import annotations

from enum import Enum


class MotorEnvironment(str, Enum):
    """Ambientes de ejecución preparados para configuración futura."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ConfigCategory(str, Enum):
    """Categorías oficiales de configuración del Motor Inteligente."""

    GENERAL = "general"
    PATHS = "paths"
    BEHAVIOR = "behavior"
    COMMUNICATION = "communication"
    PROCESSING = "processing"
    SECURITY = "security"
    EVENTS = "events"
    PERFORMANCE = "performance"
    COMPREHENSION = "comprehension"
    CLASSIFICATION = "classification"
    COMPARATIVE_TABLES = "comparative_tables"
    INTELLIGENT_ANALYSIS = "intelligent_analysis"
    ENTERPRISE_INTEGRATION = "enterprise_integration"
    INTEGRATION_API = "integration_api"
    FUTURE = "future"
