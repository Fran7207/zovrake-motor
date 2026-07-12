"""
Motor Inteligente de ZOVRAKE.

Servicio Python independiente del ERP frontend.
Implementación 8.9 — Performance Optimization & Scalability Framework (Prompt Maestro 8).
"""

__version__ = "8.12.0"

from zovrake_motor.certification import CoreCertificationChecker
from zovrake_motor.classification import ClassificationService
from zovrake_motor.communication import CommunicationService
from zovrake_motor.comparative_tables import ComparativeTablesService
from zovrake_motor.comprehension import ComprehensionService
from zovrake_motor.config import ConfigurationProvider, MotorSettings
from zovrake_motor.context import ContextService
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.documents import DocumentService
from zovrake_motor.enterprise_integration import EnterpriseIntegrationService
from zovrake_motor.events import EventManager, EventService
from zovrake_motor.intelligent_analysis import IntelligentAnalysisService
from zovrake_motor.reception import ReceptionService
from zovrake_motor.states import MotorState, StateManager, StateService

__all__ = [
    "ClassificationService",
    "CommunicationService",
    "ComparativeTablesService",
    "ComprehensionService",
    "ConfigurationProvider",
    "ContextService",
    "CoreCertificationChecker",
    "DocumentService",
    "EnterpriseIntegrationService",
    "EventManager",
    "EventService",
    "IntelligentAnalysisService",
    "MotorState",
    "MotorCoordinator",
    "MotorSettings",
    "ReceptionService",
    "StateManager",
    "StateService",
    "__version__",
]
