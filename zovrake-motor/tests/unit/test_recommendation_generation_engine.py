"""Pruebas del Recommendation Generation Engine — Implementación 7.7."""

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
    RecommendationInputAccessError,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.enums import (
    ConfidenceLevel,
    RecommendationGenerationStatus,
    RecommendationScenarioType,
)
from zovrake_motor.intelligent_analysis.recommendation_generation_engine.governance import (
    EXPECTED_CONFIDENCE_LEVELS,
    EXPECTED_RECOMMENDATION_SCENARIOS,
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


def _build_full_analysis_bundle_with_explanations(
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
    return (
        eae_result.catalog,
        cee_result.catalog,
        rae_result.catalog,
        cxee_result.catalog,
        ege_result.catalog,
        definitive_catalog,
        process_id,
    )


class TestRecommendationGenerationBuilderEngine:
    def test_engine_initializes_with_one_generator(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_generates_recommendations_from_full_analysis_bundle(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations()
        )

        result = engine.generate(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert result.explanation_catalog_preserved is True
        assert result.definitive_catalog_preserved is True
        assert result.status in (
            RecommendationGenerationStatus.GENERATED,
            RecommendationGenerationStatus.PARTIAL,
        )
        assert result.catalog.reasoning_result_builder_prepared is True
        assert len(result.catalog.profiles) >= 1

    def test_preserves_all_inputs_without_modification(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations()
        )
        evidence_snapshot = evidence_catalog.to_dict()
        explanation_snapshot = explanation_catalog.to_dict()
        definitive_snapshot = str(definitive_catalog)

        engine.generate(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_snapshot
        assert explanation_catalog.to_dict() == explanation_snapshot
        assert str(definitive_catalog) == definitive_snapshot

    def test_recommendations_are_backed_by_evidence(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations(
                extra_providers=["PROV-001", "PROV-002"],
                extra_commercial={"Precio": 1000, "Material": "Acero"},
            )
        )

        result = engine.generate(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        assert profile.scenario_type.value in EXPECTED_RECOMMENDATION_SCENARIOS
        assert profile.confidence_level.value in EXPECTED_CONFIDENCE_LEVELS
        assert profile.justification.why_issued
        assert profile.traceability_ref.definitive_model_id

    def test_supports_clear_winner_or_equivalent_or_insufficient_scenarios(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations()
        )

        result = engine.generate(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        if profile.scenario_type == RecommendationScenarioType.CLEAR_WINNER:
            assert profile.recommended_provider_id is not None
            assert profile.supporting_evidence_ids
        elif profile.scenario_type == RecommendationScenarioType.EQUIVALENT_ALTERNATIVES:
            assert profile.recommended_provider_id is None
            assert len(profile.equivalent_alternatives) >= 2
        elif profile.scenario_type == RecommendationScenarioType.INSUFFICIENT_INFORMATION:
            assert profile.recommended_provider_id is None
            assert profile.suggested_actions or profile.missing_documentation

    def test_never_recommends_without_supporting_evidence_for_clear_winner(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations(extra_providers=["PROV-001", "PROV-002"])
        )

        result = engine.generate(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        if profile.scenario_type == RecommendationScenarioType.CLEAR_WINNER:
            assert profile.supporting_evidence_ids
            assert profile.justification.supporting_evidence_ids

    def test_rejects_invalid_input_bundle(self):
        engine = RecommendationGenerationBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(RecommendationInputAccessError):
            engine.generate(
                RecommendationGenerationRequest(
                    process_id=process_id,
                    evidence_catalog={"catalog_id": "invalid"},
                    consistency_catalog={"catalog_id": "invalid"},
                    risk_catalog={"catalog_id": "invalid"},
                    context_catalog={"catalog_id": "invalid"},
                    explanation_catalog={"catalog_id": "invalid"},
                    definitive_catalog={"catalog_id": "invalid"},
                ),
            )


class TestRecommendationGenerationIntegration:
    def test_service_generates_recommendations_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations()
        )

        result = service.generate_recommendations(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.definitive_catalog_preserved is True
        assert service.recommendation_generation_engine is not None
        assert service.recommendation_generation_engine.registry.count() == 1

    def test_pipeline_phase_includes_recommendation_generation(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.GENERACION_EXPLICACIONES) < phases.index(
            IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES,
        )
        assert (
            IntelligentAnalysisPipeline.recommendation_generation_phase()
            == IntelligentAnalysisPhase.GENERACION_RECOMENDACIONES
        )

    def test_states_and_events_during_recommendation_generation(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, explanation_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_explanations(extra_providers=["PROV-001"])
        )

        service.generate_recommendations(
            RecommendationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                explanation_catalog=explanation_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_rge(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().recommendation_generation_engine
        assert settings.enabled is True
        assert settings.organized_recommendation_generator_enabled is True
        assert settings.reasoning_result_builder_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module(
            "zovrake_motor.intelligent_analysis.recommendation_generation_engine",
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

    def test_full_pipeline_chain_preserves_data(self):
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

        assert rge_result.explanation_catalog_preserved is True
        assert rge_result.catalog.reasoning_result_builder_prepared is True
        if rge_result.catalog.profiles:
            profile = rge_result.catalog.profiles[0]
            assert profile.confidence_level in (
                ConfidenceLevel.HIGH,
                ConfidenceLevel.MEDIUM,
                ConfidenceLevel.LOW,
            )
