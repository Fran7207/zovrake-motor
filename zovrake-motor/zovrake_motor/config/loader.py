"""Carga de configuración del Motor Inteligente."""

from __future__ import annotations

from zovrake_motor.config.categories import (
    BehaviorSettings,
    ClassificationSettings,
    CommunicationSettings,
    ComparativeTablesSettings,
    IntelligentAnalysisSettings,
    ComprehensionSettings,
    EventsSettings,
    FutureSettings,
    GeneralSettings,
    PathsSettings,
    PerformanceSettings,
    ProcessingSettings,
    SecuritySettings,
)
from zovrake_motor.config.enums import MotorEnvironment
from zovrake_motor.config.motor_configuration import MotorConfiguration


class ConfigurationLoader:
    """
    Construye la configuración del Motor según el ambiente.

    En esta etapa no realiza lectura de archivos externos ni variables de entorno.
    """

    @classmethod
    def load(cls, *, environment: MotorEnvironment | None = None) -> MotorConfiguration:
        env = environment or MotorEnvironment.DEVELOPMENT
        return MotorConfiguration(
            general=GeneralSettings.for_environment(env),
            paths=PathsSettings.default(),
            behavior=BehaviorSettings.default(),
            communication=CommunicationSettings.default(),
            processing=ProcessingSettings.default(),
            security=SecuritySettings.default(),
            events=EventsSettings.default(),
            performance=PerformanceSettings.default(),
            comprehension=ComprehensionSettings.default(),
            classification=ClassificationSettings.default(),
            comparative_tables=ComparativeTablesSettings.default(),
            intelligent_analysis=IntelligentAnalysisSettings.default(),
            future=FutureSettings.default(),
        )

    @classmethod
    def from_general(cls, general: GeneralSettings) -> MotorConfiguration:
        """Compatibilidad con configuración general preexistente."""
        return MotorConfiguration(general=general)
