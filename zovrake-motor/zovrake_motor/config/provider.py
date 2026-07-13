"""
Proveedor centralizado de configuración del Motor Inteligente.

Única fuente oficial de configuración para todos los módulos.
"""

from __future__ import annotations

from typing import Any

from zovrake_motor.config.categories import (
    BehaviorSettings,
    ClassificationSettings,
    CommunicationSettings,
    ComparativeTablesSettings,
    ComprehensionSettings,
    EventsSettings,
    FutureSettings,
    GeneralSettings,
    EnterpriseIntegrationSettings,
    IntegrationApiSettings,
    IntelligentAnalysisSettings,
    PathsSettings,
    PerformanceSettings,
    ProcessingSettings,
    SecuritySettings,
)
from zovrake_motor.config.enums import ConfigCategory, MotorEnvironment
from zovrake_motor.config.loader import ConfigurationLoader
from zovrake_motor.config.motor_configuration import MotorConfiguration
from zovrake_motor.config.validator import ConfigurationValidator


class ConfigurationProvider:
    """
    Punto de acceso uniforme a la configuración del Motor.

    Todos los módulos y el Coordinator deben obtener configuración desde aquí.
    """

    def __init__(
        self,
        configuration: MotorConfiguration | None = None,
        *,
        validate: bool = True,
    ) -> None:
        self._configuration = configuration or ConfigurationLoader.load()
        if validate:
            ConfigurationValidator().validate(self._configuration)

    @classmethod
    def default(cls) -> ConfigurationProvider:
        return cls()

    @classmethod
    def for_environment(cls, environment: MotorEnvironment) -> ConfigurationProvider:
        configuration = ConfigurationLoader.load(environment=environment)
        return cls(configuration)

    @classmethod
    def from_general(cls, general: GeneralSettings) -> ConfigurationProvider:
        configuration = ConfigurationLoader.from_general(general)
        return cls(configuration)

    @property
    def configuration(self) -> MotorConfiguration:
        return self._configuration

    def general(self) -> GeneralSettings:
        return self._configuration.general

    def paths(self) -> PathsSettings:
        return self._configuration.paths

    def behavior(self) -> BehaviorSettings:
        return self._configuration.behavior

    def communication(self) -> CommunicationSettings:
        return self._configuration.communication

    def processing(self) -> ProcessingSettings:
        return self._configuration.processing

    def security(self) -> SecuritySettings:
        return self._configuration.security

    def events(self) -> EventsSettings:
        return self._configuration.events

    def performance(self) -> PerformanceSettings:
        return self._configuration.performance

    def comprehension(self) -> ComprehensionSettings:
        return self._configuration.comprehension

    def classification(self) -> ClassificationSettings:
        return self._configuration.classification

    def comparative_tables(self) -> ComparativeTablesSettings:
        return self._configuration.comparative_tables

    def intelligent_analysis(self) -> IntelligentAnalysisSettings:
        return self._configuration.intelligent_analysis

    def enterprise_integration(self) -> EnterpriseIntegrationSettings:
        return self._configuration.enterprise_integration

    def integration_api(self) -> IntegrationApiSettings:
        return self._configuration.integration_api

    def future(self) -> FutureSettings:
        return self._configuration.future

    def get_category(self, category: ConfigCategory) -> Any:
        return self._configuration.get_category(category)

    def service_name(self) -> str:
        return self.general().service_name

    def service_version(self) -> str:
        return self.general().service_version

    def environment(self) -> MotorEnvironment:
        return self.general().environment

    def snapshot(self) -> dict[str, Any]:
        return self._configuration.to_dict()
