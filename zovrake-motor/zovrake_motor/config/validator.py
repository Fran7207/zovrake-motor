"""Validación estructural de la configuración del Motor Inteligente."""

from __future__ import annotations

from zovrake_motor.config.exceptions import ConfigurationError
from zovrake_motor.config.motor_configuration import MotorConfiguration


class ConfigurationValidator:
    """
    Valida la consistencia básica de la configuración antes del arranque.

    No aplica reglas de negocio ni validaciones complejas en esta etapa.
    """

    def validate(self, configuration: MotorConfiguration) -> None:
        errors: list[str] = []

        if not configuration.general.service_name.strip():
            errors.append("general.service_name no puede estar vacío")

        if not configuration.general.service_version.strip():
            errors.append("general.service_version no puede estar vacío")

        if configuration.processing.max_concurrent_processes < 1:
            errors.append("processing.max_concurrent_processes debe ser >= 1")

        if configuration.events.max_events_in_memory < 1:
            errors.append("events.max_events_in_memory debe ser >= 1")

        for root_name, root_value in (
            ("paths.data_root", configuration.paths.data_root),
            ("paths.temp_root", configuration.paths.temp_root),
            ("paths.logs_root", configuration.paths.logs_root),
        ):
            if not root_value.strip():
                errors.append(f"{root_name} no puede estar vacío")

        if errors:
            raise ConfigurationError("; ".join(errors))
