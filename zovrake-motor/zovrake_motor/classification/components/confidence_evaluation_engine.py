"""Confidence Evaluation Engine — estructura preparatoria."""

from zovrake_motor.classification.components.base import ClassificationComponentPort


class ConfidenceEvaluationEngine(ClassificationComponentPort):
    """Responsabilidad futura: evaluar niveles de confianza en clasificaciones."""

    @property
    def component_name(self) -> str:
        return "confidence_evaluation_engine"

    @property
    def component_label(self) -> str:
        return "Confidence Evaluation Engine"

    def is_ready(self) -> bool:
        return False
