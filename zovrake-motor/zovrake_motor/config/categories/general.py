"""Configuración general del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass, field

from zovrake_motor.config.enums import MotorEnvironment


@dataclass(frozen=True)
class GeneralSettings:
    """Identidad y parámetros generales del Motor."""

    service_name: str = "zovrake-motor"
    service_version: str = "8.12.0"
    environment: MotorEnvironment = MotorEnvironment.DEVELOPMENT
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def default(cls) -> GeneralSettings:
        return cls()

    @classmethod
    def for_environment(cls, environment: MotorEnvironment) -> GeneralSettings:
        return cls(environment=environment)
