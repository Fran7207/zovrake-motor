"""Categorías de configuración del Motor Inteligente."""

from zovrake_motor.config.categories.behavior import BehaviorSettings
from zovrake_motor.config.categories.classification import ClassificationSettings, ConceptAnalysisSettings, ConceptNormalizationSettings, EquivalenceDetectionSettings, MaterialClassificationSettings, ServiceClassificationSettings
from zovrake_motor.config.categories.enterprise_integration import EnterpriseIntegrationSettings
from zovrake_motor.config.categories.intelligent_analysis import IntelligentAnalysisSettings
from zovrake_motor.config.categories.comparative_tables import (
    ComparativeStructureEngineSettings,
    DynamicColumnBuilderSettings,
    ComparativeTablesSettings,
)
from zovrake_motor.config.categories.communication import CommunicationSettings
from zovrake_motor.config.categories.comprehension import (
    ComprehensionSettings,
    DocumentAdapterSettings,
    DocumentCanonicalSettings,
    DocumentContextIntegrationSettings,
    DocumentExtractionSettings,
    DocumentInternalModelSettings,
    DocumentKnowledgeIndexSettings,
    DocumentRecognitionSettings,
    DocumentValidationSettings,
)
from zovrake_motor.config.categories.events import EventsSettings
from zovrake_motor.config.categories.future import FutureSettings
from zovrake_motor.config.categories.general import GeneralSettings
from zovrake_motor.config.categories.paths import PathsSettings
from zovrake_motor.config.categories.performance import PerformanceSettings
from zovrake_motor.config.categories.processing import ProcessingSettings
from zovrake_motor.config.categories.security import SecuritySettings

__all__ = [
    "BehaviorSettings",
    "ClassificationSettings",
    "ConceptAnalysisSettings",
    "ConceptNormalizationSettings",
    "EquivalenceDetectionSettings",
    "MaterialClassificationSettings",
    "ServiceClassificationSettings",
    "CommunicationSettings",
    "EnterpriseIntegrationSettings",
    "IntelligentAnalysisSettings",
    "DynamicColumnBuilderSettings",
    "ComparativeTablesSettings",
    "ComprehensionSettings",
    "DocumentAdapterSettings",
    "DocumentCanonicalSettings",
    "DocumentContextIntegrationSettings",
    "DocumentExtractionSettings",
    "DocumentInternalModelSettings",
    "DocumentKnowledgeIndexSettings",
    "DocumentRecognitionSettings",
    "DocumentValidationSettings",
    "EventsSettings",
    "FutureSettings",
    "GeneralSettings",
    "PathsSettings",
    "PerformanceSettings",
    "ProcessingSettings",
    "SecuritySettings",
]
