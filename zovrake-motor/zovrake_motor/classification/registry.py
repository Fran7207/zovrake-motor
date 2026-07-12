"""Registro extensible de componentes internos de Clasificación Inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.components.comparable_group_builder import ComparableGroupBuilder
from zovrake_motor.classification.components.comparative_domain_model_builder import (
    ComparativeDomainModelBuilder,
)
from zovrake_motor.classification.components.classification_quality_framework import (
    ClassificationQualityFramework,
)
from zovrake_motor.classification.components.concept_analysis_engine import ConceptAnalysisEngineComponent
from zovrake_motor.classification.components.concept_normalization_engine import (
    ConceptNormalizationEngineComponent,
)
from zovrake_motor.classification.components.confidence_evaluation_engine import (
    ConfidenceEvaluationEngine,
)
from zovrake_motor.classification.components.context_association_engine import ContextAssociationEngineComponent
from zovrake_motor.classification.components.equivalence_detection_engine import (
    EquivalenceDetectionEngineComponent,
)
from zovrake_motor.classification.components.group_identifier_generator import GroupIdentifierGenerator
from zovrake_motor.classification.components.material_classification_engine import (
    MaterialClassificationEngineComponent,
)
from zovrake_motor.classification.components.service_classification_engine import (
    ServiceClassificationEngineComponent,
)
from zovrake_motor.classification.components.traceability_manager import ClassificationTraceabilityManager

if TYPE_CHECKING:
    from zovrake_motor.classification.components.classification_coordinator import ClassificationCoordinator
    from zovrake_motor.config.provider import ConfigurationProvider


class ComponentRegistry:
    """
    Registro de componentes del módulo de Clasificación Inteligente.

    Permite incorporar nuevos clasificadores mediante extensión sin modificar el núcleo.
    """

    def __init__(self) -> None:
        self._components: dict[str, ClassificationComponentPort] = {}

    def register(self, component: ClassificationComponentPort) -> None:
        self._components[component.component_name] = component

    def register_defaults(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
    ) -> ClassificationCoordinator:
        """Registra la estructura base de componentes preparada para PM5."""
        from zovrake_motor.classification.components.classification_coordinator import (
            ClassificationCoordinator,
        )

        _ = config_provider  # reservado para configuración futura por componente

        components: tuple[ClassificationComponentPort, ...] = (
            ConceptAnalysisEngineComponent(config_provider=config_provider),
            MaterialClassificationEngineComponent(config_provider=config_provider),
            ServiceClassificationEngineComponent(config_provider=config_provider),
            ConceptNormalizationEngineComponent(config_provider=config_provider),
            EquivalenceDetectionEngineComponent(config_provider=config_provider),
            ComparableGroupBuilder(config_provider=config_provider),
            GroupIdentifierGenerator(),
            ContextAssociationEngineComponent(config_provider=config_provider),
            ClassificationTraceabilityManager(),
            ConfidenceEvaluationEngine(),
            ComparativeDomainModelBuilder(config_provider=config_provider),
            ClassificationQualityFramework(config_provider=config_provider),
        )

        for component in components:
            self.register(component)

        coordinator = ClassificationCoordinator(self)
        self.register(coordinator)
        return coordinator

    def get(self, name: str) -> ClassificationComponentPort | None:
        return self._components.get(name)

    def all_components(self) -> tuple[ClassificationComponentPort, ...]:
        return tuple(self._components.values())

    def count(self) -> int:
        return len(self._components)

    def ready_count(self) -> int:
        return sum(1 for component in self._components.values() if component.is_ready())

    def snapshot(self) -> list[dict[str, Any]]:
        return [component.snapshot() for component in self._components.values()]
