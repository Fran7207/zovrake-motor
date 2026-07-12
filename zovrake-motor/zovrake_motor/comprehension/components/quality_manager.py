"""Gestor de Calidad Documental — estructura preparatoria."""

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort


class DocumentQualityManager(ComprehensionComponentPort):
    """Responsabilidad futura: evaluar calidad y completitud del contenido documental."""

    @property
    def component_name(self) -> str:
        return "quality_manager"

    @property
    def component_label(self) -> str:
        return "Gestor de Calidad Documental"

    def is_ready(self) -> bool:
        return False
