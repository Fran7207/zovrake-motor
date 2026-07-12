"""Gestor de Trazabilidad Documental — estructura preparatoria."""

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort


class DocumentTraceabilityManager(ComprehensionComponentPort):
    """Responsabilidad futura: registrar trazabilidad del procesamiento documental."""

    @property
    def component_name(self) -> str:
        return "traceability_manager"

    @property
    def component_label(self) -> str:
        return "Gestor de Trazabilidad"

    def is_ready(self) -> bool:
        return False
