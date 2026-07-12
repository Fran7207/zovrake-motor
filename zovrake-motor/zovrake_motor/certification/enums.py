"""Enumeraciones del sistema de certificación arquitectónica."""

from __future__ import annotations

from enum import Enum


class CertificationArea(str, Enum):
    """Áreas evaluadas en la certificación del núcleo."""

    INITIALIZATION = "initialization"
    ARCHITECTURE = "architecture"
    COORDINATOR = "coordinator"
    MODULES = "modules"
    PIPELINE = "pipeline"
    STATE_MANAGEMENT = "state_management"
    EVENT_MANAGEMENT = "event_management"
    CONFIGURATION = "configuration"
    PROMPT_MAESTRO_4 = "prompt_maestro_4"
    COMPREHENSION_MODULE = "comprehension_module"
    PROMPT_MAESTRO_5 = "prompt_maestro_5"
    CLASSIFICATION_MODULE = "classification_module"
    CLASSIFICATION_MODULE_CLOSURE = "classification_module_closure"
    PROMPT_MAESTRO_6 = "prompt_maestro_6"
    COMPARATIVE_TABLES_MODULE = "comparative_tables_module"
    PROMPT_MAESTRO_7 = "prompt_maestro_7"
    INTELLIGENT_ANALYSIS_MODULE = "intelligent_analysis_module"
    INTELLIGENT_ANALYSIS_MODULE_CLOSURE = "intelligent_analysis_module_closure"
    PROMPT_MAESTRO_8 = "prompt_maestro_8"
    ENTERPRISE_INTEGRATION_E2E = "enterprise_integration_e2e"
    ENTERPRISE_INTEGRATION_PLATFORM = "enterprise_integration_platform"
    ENTERPRISE_INTEGRATION_CLOSURE = "enterprise_integration_closure"


class CertificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
