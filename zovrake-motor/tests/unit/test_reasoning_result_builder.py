"""Pruebas del Reasoning Result Builder — Implementación 7.8."""

from __future__ import annotations

import copy
import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

import pytest

from zovrake_motor import IntelligentAnalysisService
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine import (
    ConsistencyEvaluationBuilderEngine,
    ConsistencyEvaluationRequest,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine import (
    ContextEvaluationBuilderEngine,
    ContextEvaluationRequest,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine import (
    EvidenceAnalysisBuilderEngine,
    EvidenceAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine import (
    ExplanationGenerationBuilderEngine,
    ExplanationGenerationRequest,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine import (
    RecommendationGenerationBuilderEngine,
    RecommendationGenerationRequest,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder import (
    ReasoningResultBuilderEngine,
    ReasoningResultBuildRequest,
    ReasoningResultInputAccessError,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.enums import (
    ReasoningResultBuildStatus,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.governance import (
    PM7_OUTPUT_CATALOG_CONTRACT_NAME,
    PM7_OUTPUT_CONTRACT_NAME,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine import (
    RiskAnalysisBuilderEngine,
    RiskAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_validation_framework import build_definitive_catalog


def _build_full_analysis_bundle_with_recommendations(
    *,
    process_id=None,
    extra_providers=None,
    extra_commercial=None,
):
    process_id = process_id or uuid4()
    definitive_catalog, _ = build_definitive_catalog(
        process_id=process_id,
        extra_providers=extra_providers or ["PROV-001", "PROV-002"],
        extra_commercial=extra_commercial or {"Precio": 1000},
    )
    eae_engine = EvidenceAnalysisBuilderEngine()
    eae_engine.initialize()
    eae_result = eae_engine.analyze(
        EvidenceAnalysisRequest(
            process_id=process_id,
            definitive_catalog=definitive_catalog,
        ),
    )
    cee_engine = ConsistencyEvaluationBuilderEngine()
    cee_engine.initialize()
    cee_result = cee_engine.evaluate(
        ConsistencyEvaluationRequest(
            process_id=process_id,
            evidence_catalog=eae_result.catalog,
        ),
    )
    rae_engine = RiskAnalysisBuilderEngine()
    rae_engine.initialize()
    rae_result = rae_engine.analyze(
        RiskAnalysisRequest(
            process_id=process_id,
            evidence_catalog=eae_result.catalog,
            consistency_catalog=cee_result.catalog,
        ),
    )
    cxee_engine = ContextEvaluationBuilderEngine()
    cxee_engine.initialize()
    cxee_result = cxee_engine.evaluate(
        ContextEvaluationRequest(
            process_id=process_id,
            evidence_catalog=eae_result.catalog,
            consistency_catalog=cee_result.catalog,
            risk_catalog=rae_result.catalog,
            definitive_catalog=definitive_catalog,
            requirement_context=dict(
                definitive_catalog["models"][0].get("inherited_context", {}),
            ),
        ),
    )
    ege_engine = ExplanationGenerationBuilderEngine()
    ege_engine.initialize()
    ege_result = ege_engine.generate(
        ExplanationGenerationRequest(
            process_id=process_id,
            evidence_catalog=eae_result.catalog,
            consistency_catalog=cee_result.catalog,
            risk_catalog=rae_result.catalog,
            context_catalog=cxee_result.catalog,
            definitive_catalog=definitive_catalog,
        ),
    )
    rge_engine = RecommendationGenerationBuilderEngine()
    rge_engine.initialize()
    rge_result = rge_engine.generate(
        RecommendationGenerationRequest(
            process_id=process_id,
            evidence_catalog=eae_result.catalog,
            consistency_catalog=cee_result.catalog,
            risk_catalog=rae_result.catalog,
            context_catalog=cxee_result.catalog,
            explanation_catalog=ege_result.catalog,
            definitive_catalog=definitive_catalog,
        ),
    )
    return (
        eae_result.catalog,
        cee_result.catalog,
        rae_result.catalog,
        cxee_result.catalog,
        ege_result.catalog,
        rge_result.catalog,
        definitive_catalog,
        process_id,
    )


class TestReasoningResultBuilderEngine:
    def test_engine_initializes_with_one_builder(self):
        engine = ReasoningResultBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_builds_one_result_per_comparable_group(self):
        engine = ReasoningResultBuilderEngine()
        engine.initialize()
        (
            evidence_catalog,
            consistency_catalog,
            risk_catalog,
            context_catalog,
            explanation_catalog,
            recommendation_catalog,
            definitive_catalog,
            process_id,
        ) = _build_full_analysis_bundle_with_recommendations()

        result = engine.build(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                recommendation_catalog=recommendation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.status in (
            ReasoningResultBuildStatus.BUILT,
            ReasoningResultBuildStatus.PARTIAL,
        )
        assert result.results_count >= 1
        assert len(result.catalog.results) == result.results_count
        assert result.catalog.integration_certification_framework_prepared is True

    def test_result_contains_required_contract_fields(self):
        engine = ReasoningResultBuilderEngine()
        engine.initialize()
        (
            evidence_catalog,
            consistency_catalog,
            risk_catalog,
            context_catalog,
            explanation_catalog,
            recommendation_catalog,
            definitive_catalog,
            process_id,
        ) = _build_full_analysis_bundle_with_recommendations()

        result = engine.build(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                recommendation_catalog=recommendation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        group_result = result.catalog.results[0]
        payload = group_result.to_dict()

        assert payload["contract_name"] == PM7_OUTPUT_CONTRACT_NAME
        assert result.catalog.to_dict()["contract_name"] == PM7_OUTPUT_CATALOG_CONTRACT_NAME
        assert group_result.result_id
        assert group_result.group_id
        assert group_result.definitive_model_id
        assert group_result.executive_summary
        assert group_result.structured_explanation
        assert group_result.recommendation
        assert group_result.confidence_level
        assert group_result.document_traceability.definitive_model_id
        assert group_result.source_data_preserved is True

    def test_preserves_all_inputs_without_modification(self):
        engine = ReasoningResultBuilderEngine()
        engine.initialize()
        (
            evidence_catalog,
            consistency_catalog,
            risk_catalog,
            context_catalog,
            explanation_catalog,
            recommendation_catalog,
            definitive_catalog,
            process_id,
        ) = _build_full_analysis_bundle_with_recommendations()

        evidence_snapshot = evidence_catalog.to_dict()
        recommendation_snapshot = recommendation_catalog.to_dict()
        definitive_snapshot = copy.deepcopy(definitive_catalog)

        engine.build(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                recommendation_catalog=recommendation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_snapshot
        assert recommendation_catalog.to_dict() == recommendation_snapshot
        assert definitive_catalog == definitive_snapshot

    def test_rejects_invalid_input_bundle(self):
        engine = ReasoningResultBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(ReasoningResultInputAccessError):
            engine.build(
                ReasoningResultBuildRequest(
                    process_id=process_id,
                    evidence_catalog={"catalog_id": "invalid"},
                    consistency_catalog={"catalog_id": "invalid"},
                    risk_catalog={"catalog_id": "invalid"},
                    context_catalog={"catalog_id": "invalid"},
                    explanation_catalog={"catalog_id": "invalid"},
                    recommendation_catalog={"catalog_id": "invalid"},
                    definitive_catalog={"catalog_id": "invalid"},
                ),
            )


class TestReasoningResultBuilderIntegration:
    def test_service_builds_results_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        (
            evidence_catalog,
            consistency_catalog,
            risk_catalog,
            context_catalog,
            explanation_catalog,
            recommendation_catalog,
            definitive_catalog,
            process_id,
        ) = _build_full_analysis_bundle_with_recommendations()

        result = service.build_intelligent_analysis_results(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                recommendation_catalog=recommendation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.recommendation_catalog_preserved is True
        assert service.reasoning_result_builder is not None
        assert service.reasoning_result_builder.registry.count() == 1

    def test_pipeline_phase_includes_reasoning_result_build(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES) < phases.index(
            IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE,
        )
        assert (
            IntelligentAnalysisPipeline.reasoning_result_build_phase()
            == IntelligentAnalysisPhase.CONSTRUCCION_RESULTADO_ANALISIS_INTELIGENTE
        )

    def test_states_and_events_during_reasoning_result_build(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        (
            evidence_catalog,
            consistency_catalog,
            risk_catalog,
            context_catalog,
            explanation_catalog,
            recommendation_catalog,
            definitive_catalog,
            process_id,
        ) = _build_full_analysis_bundle_with_recommendations(extra_providers=["PROV-001"])

        service.build_intelligent_analysis_results(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                recommendation_catalog=recommendation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_rrb(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().reasoning_result_builder
        assert settings.enabled is True
        assert settings.organized_result_builder_enabled is True
        assert settings.integration_certification_framework_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module(
            "zovrake_motor.intelligent_analysis.reasoning_result_builder",
        )
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            package.__path__,
            prefix=package.__name__ + ".",
        ):
            module = importlib.import_module(modname)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            content = Path(source).read_text(encoding="utf-8")
            assert "zovrake_motor.comparative_tables" not in content

    def test_full_pipeline_chain_produces_official_output_contract(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 2500},
        )
        requirement_context = dict(definitive_catalog["models"][0].get("inherited_context", {}))

        eae_result = service.analyze_evidence(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )
        cee_result = service.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
            ),
        )
        rae_result = service.analyze_risks(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
                consistency_catalog=cee_result.catalog,
            ),
        )
        cxee_result = service.evaluate_context(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
                consistency_catalog=cee_result.catalog,
                risk_catalog=rae_result.catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )
        ege_result = service.generate_explanations(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
                consistency_catalog=cee_result.catalog,
                risk_catalog=rae_result.catalog,
                context_catalog=cxee_result.catalog,
                definitive_catalog=definitive_catalog,
            ),
        )
        rge_result = service.generate_recommendations(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
                consistency_catalog=cee_result.catalog,
                risk_catalog=rae_result.catalog,
                context_catalog=cxee_result.catalog,
                explanation_catalog=ege_result.catalog,
                definitive_catalog=definitive_catalog,
            ),
        )
        rrb_result = service.build_intelligent_analysis_results(
            ReasoningResultBuildRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
                consistency_catalog=cee_result.catalog,
                risk_catalog=rae_result.catalog,
                context_catalog=cxee_result.catalog,
                explanation_catalog=ege_result.catalog,
                recommendation_catalog=rge_result.catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert rrb_result.source_data_preserved is True
        assert rrb_result.catalog.results
        assert rrb_result.catalog.to_dict()["contract_name"] == PM7_OUTPUT_CATALOG_CONTRACT_NAME
