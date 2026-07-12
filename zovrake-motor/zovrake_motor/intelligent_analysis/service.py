"""Servicio del Módulo de Razonamiento y Resultado del Análisis Inteligente."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.config.accessible import ConfigurationAccessible
from zovrake_motor.events.manager import EventManager
from zovrake_motor.intelligent_analysis.components.intelligent_analysis_coordinator import (
    IntelligentAnalysisCoordinator,
)
from zovrake_motor.intelligent_analysis.input_gateway import ComparativeTablesOutputGateway
from zovrake_motor.intelligent_analysis.integration import IntelligentAnalysisMotorIntegration
from zovrake_motor.intelligent_analysis.components.evidence_analysis_engine import (
    EvidenceAnalysisEngine,
)
from zovrake_motor.intelligent_analysis.components.consistency_evaluation_engine import (
    ConsistencyEvaluationEngine,
)
from zovrake_motor.intelligent_analysis.components.risk_analysis_engine import (
    RiskAnalysisEngine,
)
from zovrake_motor.intelligent_analysis.components.context_evaluation_engine import (
    ContextEvaluationEngine,
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
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisRequest,
    EvidenceAnalysisResult,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.models import (
    ConsistencyEvaluationRequest,
    ConsistencyEvaluationResult,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.models import (
    RiskAnalysisRequest,
    RiskAnalysisResult,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.models import (
    ContextEvaluationRequest,
    ContextEvaluationResult,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.models import (
    ExplanationGenerationRequest,
    ExplanationGenerationResult,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.models import (
    RecommendationGenerationRequest,
    RecommendationGenerationResult,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.models import (
    ReasoningResultBuildRequest,
    ReasoningResultBuildResult,
)
from zovrake_motor.intelligent_analysis.models import (
    IntelligentAnalysisRequest,
    IntelligentAnalysisResult,
)
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.intelligent_analysis.port import IntelligentAnalysisPort
from zovrake_motor.intelligent_analysis.registry import ComponentRegistry
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class IntelligentAnalysisService(ConfigurationAccessible, ModulePort, IntelligentAnalysisPort):
    """
    Módulo de Razonamiento y Resultado del Análisis Inteligente.

    Responsabilidad única: analizar el Modelo Comparativo Definitivo y producir
    un Resultado del Análisis Inteligente explicable y basado en evidencias.
    """

    MODULE_NAME = "intelligent_analysis"

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
        component_registry: ComponentRegistry | None = None,
        integration: IntelligentAnalysisMotorIntegration | None = None,
        comparative_tables_gateway: ComparativeTablesOutputGateway | None = None,
    ) -> None:
        super().__init__(config_provider=config_provider)
        self._integration = integration or IntelligentAnalysisMotorIntegration(
            config_provider=config_provider,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        self._registry = component_registry or ComponentRegistry()
        self._intelligent_analysis_coordinator: IntelligentAnalysisCoordinator | None = None
        self._comparative_tables_gateway = comparative_tables_gateway
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self.MODULE_NAME

    @property
    def component_registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def intelligent_analysis_coordinator(self) -> IntelligentAnalysisCoordinator | None:
        return self._intelligent_analysis_coordinator

    @property
    def comparative_tables_gateway(self) -> ComparativeTablesOutputGateway:
        if self._comparative_tables_gateway is None:
            self._comparative_tables_gateway = ComparativeTablesOutputGateway(
                settings=self._integration.intelligent_analysis_settings(),
            )
        return self._comparative_tables_gateway

    @property
    def integration(self) -> IntelligentAnalysisMotorIntegration:
        return self._integration

    @property
    def state_manager(self) -> StateManager:
        return self._integration.state_manager

    @property
    def event_manager(self) -> EventManager:
        return self._integration.event_manager

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._intelligent_analysis_coordinator = self._registry.register_defaults(
            config_provider=self._config_provider,
        )
        for component in self._registry.all_components():
            component.initialize()
        self._comparative_tables_gateway = ComparativeTablesOutputGateway(
            settings=self._integration.intelligent_analysis_settings(),
        )
        self._initialized = True

    @property
    def evidence_analysis_engine(self):
        component = self._registry.get("evidence_analysis_engine")
        if isinstance(component, EvidenceAnalysisEngine):
            return component.engine
        return None

    @property
    def consistency_evaluation_engine(self):
        component = self._registry.get("consistency_evaluation_engine")
        if isinstance(component, ConsistencyEvaluationEngine):
            return component.engine
        return None

    @property
    def risk_analysis_engine(self):
        component = self._registry.get("risk_analysis_engine")
        if isinstance(component, RiskAnalysisEngine):
            return component.engine
        return None

    @property
    def context_evaluation_engine(self):
        component = self._registry.get("context_evaluation_engine")
        if isinstance(component, ContextEvaluationEngine):
            return component.engine
        return None

    @property
    def explanation_generation_engine(self):
        component = self._registry.get("explanation_generation_engine")
        if isinstance(component, ExplanationGenerationEngine):
            return component.engine
        return None

    @property
    def recommendation_generation_engine(self):
        component = self._registry.get("recommendation_generation_engine")
        if isinstance(component, RecommendationGenerationEngine):
            return component.engine
        return None

    @property
    def reasoning_result_builder(self):
        component = self._registry.get("reasoning_result_builder")
        if isinstance(component, ReasoningResultBuilder):
            return component.engine
        return None

    def analyze_evidence(
        self,
        request: EvidenceAnalysisRequest,
    ) -> EvidenceAnalysisResult:
        return IntelligentAnalysisPipeline.execute_evidence_analysis(
            self._registry,
            request,
            integration=self._integration,
        )

    def evaluate_consistency(
        self,
        request: ConsistencyEvaluationRequest,
    ) -> ConsistencyEvaluationResult:
        return IntelligentAnalysisPipeline.execute_consistency_evaluation(
            self._registry,
            request,
            integration=self._integration,
        )

    def analyze_risks(
        self,
        request: RiskAnalysisRequest,
    ) -> RiskAnalysisResult:
        return IntelligentAnalysisPipeline.execute_risk_analysis(
            self._registry,
            request,
            integration=self._integration,
        )

    def evaluate_context(
        self,
        request: ContextEvaluationRequest,
    ) -> ContextEvaluationResult:
        return IntelligentAnalysisPipeline.execute_context_evaluation(
            self._registry,
            request,
            integration=self._integration,
        )

    def generate_explanations(
        self,
        request: ExplanationGenerationRequest,
    ) -> ExplanationGenerationResult:
        return IntelligentAnalysisPipeline.execute_explanation_generation(
            self._registry,
            request,
            integration=self._integration,
        )

    def generate_recommendations(
        self,
        request: RecommendationGenerationRequest,
    ) -> RecommendationGenerationResult:
        return IntelligentAnalysisPipeline.execute_recommendation_generation(
            self._registry,
            request,
            integration=self._integration,
        )

    def build_intelligent_analysis_results(
        self,
        request: ReasoningResultBuildRequest,
    ) -> ReasoningResultBuildResult:
        return IntelligentAnalysisPipeline.execute_reasoning_result_build(
            self._registry,
            request,
            integration=self._integration,
        )

    def prepare(self, request: IntelligentAnalysisRequest) -> IntelligentAnalysisResult:
        settings = self._integration.intelligent_analysis_settings()
        gateway = self.comparative_tables_gateway
        input_bundle = request.input_bundle()
        consumption = gateway.prepare_consumption(input_bundle)
        eae_engine = self.evidence_analysis_engine
        cee_engine = self.consistency_evaluation_engine
        rae_engine = self.risk_analysis_engine
        cxee_engine = self.context_evaluation_engine
        ege_engine = self.explanation_generation_engine
        rge_engine = self.recommendation_generation_engine
        rrb_engine = self.reasoning_result_builder

        return IntelligentAnalysisResult(
            process_id=request.process_id,
            prepared=True,
            message="Arquitectura de Razonamiento Inteligente preparada — sin procesamiento",
            components_ready=self._registry.ready_count(),
            metadata={
                "codigo_req": request.codigo_req,
                "enabled": settings.enabled,
                "components_count": self._registry.count(),
                "comparative_tables_consumption": consumption,
                "pm7_input_contract_required": settings.pm7_input_contract_required,
                "evidence_analyzers_registered": (
                    eae_engine.registry.count() if eae_engine else 0
                ),
                "evidence_catalog_entries_count": (
                    eae_engine.catalog_store.count() if eae_engine else 0
                ),
                "consistency_evaluators_registered": (
                    cee_engine.registry.count() if cee_engine else 0
                ),
                "consistency_catalog_entries_count": (
                    cee_engine.catalog_store.count() if cee_engine else 0
                ),
                "risk_analyzers_registered": (
                    rae_engine.registry.count() if rae_engine else 0
                ),
                "risk_catalog_entries_count": (
                    rae_engine.catalog_store.count() if rae_engine else 0
                ),
                "context_evaluators_registered": (
                    cxee_engine.registry.count() if cxee_engine else 0
                ),
                "context_catalog_entries_count": (
                    cxee_engine.catalog_store.count() if cxee_engine else 0
                ),
                "explanation_generators_registered": (
                    ege_engine.registry.count() if ege_engine else 0
                ),
                "explanation_catalog_entries_count": (
                    ege_engine.catalog_store.count() if ege_engine else 0
                ),
                "recommendation_generators_registered": (
                    rge_engine.registry.count() if rge_engine else 0
                ),
                "recommendation_catalog_entries_count": (
                    rge_engine.catalog_store.count() if rge_engine else 0
                ),
                "reasoning_result_builders_registered": (
                    rrb_engine.registry.count() if rrb_engine else 0
                ),
                "intelligent_analysis_result_catalog_entries_count": (
                    rrb_engine.catalog_store.count() if rrb_engine else 0
                ),
                "intelligent_analysis_pipeline": IntelligentAnalysisPipeline.build_snapshot(
                    self._registry,
                ),
            },
        )

    def get_intelligent_analysis_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return IntelligentAnalysisPipeline.build_snapshot(self._registry)

    def snapshot(self) -> dict[str, Any]:
        eae_engine = self.evidence_analysis_engine
        cee_engine = self.consistency_evaluation_engine
        rae_engine = self.risk_analysis_engine
        cxee_engine = self.context_evaluation_engine
        ege_engine = self.explanation_generation_engine
        rge_engine = self.recommendation_generation_engine
        rrb_engine = self.reasoning_result_builder
        return {
            "module_name": self.MODULE_NAME,
            "initialized": self._initialized,
            "integration": self._integration.snapshot(),
            "comparative_tables_gateway": self.comparative_tables_gateway.snapshot(),
            "components": self._registry.snapshot(),
            "intelligent_analysis_coordinator": (
                self._intelligent_analysis_coordinator.snapshot()
                if self._intelligent_analysis_coordinator is not None
                else None
            ),
            "evidence_analysis_engine": (
                eae_engine.snapshot() if eae_engine is not None else None
            ),
            "consistency_evaluation_engine": (
                cee_engine.snapshot() if cee_engine is not None else None
            ),
            "risk_analysis_engine": (
                rae_engine.snapshot() if rae_engine is not None else None
            ),
            "context_evaluation_engine": (
                cxee_engine.snapshot() if cxee_engine is not None else None
            ),
            "explanation_generation_engine": (
                ege_engine.snapshot() if ege_engine is not None else None
            ),
            "recommendation_generation_engine": (
                rge_engine.snapshot() if rge_engine is not None else None
            ),
            "reasoning_result_builder": (
                rrb_engine.snapshot() if rrb_engine is not None else None
            ),
            "intelligent_analysis_pipeline": self.get_intelligent_analysis_pipeline_snapshot(),
        }
