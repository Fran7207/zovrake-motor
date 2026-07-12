"""Registro extensible de componentes internos de Razonamiento Inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.intelligent_analysis.components.base import IntelligentAnalysisComponentPort
from zovrake_motor.intelligent_analysis.components.confidence_management_engine import (
    ConfidenceManagementEngine,
)
from zovrake_motor.intelligent_analysis.components.conclusion_generation_engine import (
    ConclusionGenerationEngine,
)
from zovrake_motor.intelligent_analysis.components.consistency_evaluation_engine import (
    ConsistencyEvaluationEngine,
)
from zovrake_motor.intelligent_analysis.components.context_evaluation_engine import (
    ContextEvaluationEngine,
)
from zovrake_motor.intelligent_analysis.components.evidence_analysis_engine import (
    EvidenceAnalysisEngine,
)
from zovrake_motor.intelligent_analysis.components.explanation_generation_engine import (
    ExplanationGenerationEngine,
)
from zovrake_motor.intelligent_analysis.components.recommendation_generation_engine import (
    RecommendationGenerationEngine,
)
from zovrake_motor.intelligent_analysis.components.reasoning_result_builder import (
    ReasoningResultBuilder,
)
from zovrake_motor.intelligent_analysis.components.risk_analysis_engine import RiskAnalysisEngine
from zovrake_motor.intelligent_analysis.components.traceability_management_engine import (
    TraceabilityManagementEngine,
)

if TYPE_CHECKING:
    from zovrake_motor.intelligent_analysis.components.intelligent_analysis_coordinator import (
        IntelligentAnalysisCoordinator,
    )
    from zovrake_motor.config.provider import ConfigurationProvider


class ComponentRegistry:
    """
    Registro de componentes del módulo de Razonamiento Inteligente.

    Permite incorporar nuevos motores de razonamiento mediante extensión
    sin modificar el núcleo.
    """

    def __init__(self) -> None:
        self._components: dict[str, IntelligentAnalysisComponentPort] = {}

    def register(self, component: IntelligentAnalysisComponentPort) -> None:
        self._components[component.component_name] = component

    def register_defaults(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
    ) -> IntelligentAnalysisCoordinator:
        """Registra la estructura base de componentes preparada para PM7."""
        from zovrake_motor.intelligent_analysis.components.intelligent_analysis_coordinator import (
            IntelligentAnalysisCoordinator,
        )

        components: tuple[IntelligentAnalysisComponentPort, ...] = (
            EvidenceAnalysisEngine(config_provider=config_provider),
            ConsistencyEvaluationEngine(config_provider=config_provider),
            RiskAnalysisEngine(config_provider=config_provider),
            ContextEvaluationEngine(config_provider=config_provider),
            ExplanationGenerationEngine(config_provider=config_provider),
            ConclusionGenerationEngine(config_provider=config_provider),
            RecommendationGenerationEngine(config_provider=config_provider),
            ReasoningResultBuilder(config_provider=config_provider),
            ConfidenceManagementEngine(config_provider=config_provider),
            TraceabilityManagementEngine(config_provider=config_provider),
        )

        for component in components:
            self.register(component)

        coordinator = IntelligentAnalysisCoordinator(self)
        self.register(coordinator)
        return coordinator

    def get(self, name: str) -> IntelligentAnalysisComponentPort | None:
        return self._components.get(name)

    def all_components(self) -> tuple[IntelligentAnalysisComponentPort, ...]:
        return tuple(self._components.values())

    def count(self) -> int:
        return len(self._components)

    def ready_count(self) -> int:
        return sum(1 for component in self._components.values() if component.is_ready())

    def snapshot(self) -> list[dict[str, Any]]:
        return [component.snapshot() for component in self._components.values()]
