"""Traceability Manager — estructura preparatoria."""

from zovrake_motor.classification.components.base import ClassificationComponentPort


class ClassificationTraceabilityManager(ClassificationComponentPort):
    """Responsabilidad futura: registrar trazabilidad del procesamiento de clasificación."""

    @property
    def component_name(self) -> str:
        return "traceability_manager"

    @property
    def component_label(self) -> str:
        return "Traceability Manager"

    def is_ready(self) -> bool:
        return False
