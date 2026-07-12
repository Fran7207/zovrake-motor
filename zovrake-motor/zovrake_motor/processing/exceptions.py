"""Excepciones del Pipeline Interno."""


class PipelineError(Exception):
    """Error estructural en la ejecución del Pipeline."""


class InvalidStageTransitionError(PipelineError):
    """Transición no permitida entre etapas del Pipeline."""
