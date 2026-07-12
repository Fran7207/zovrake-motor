"""Pruebas del Context Evaluation Engine — Implementación 7.5."""

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
    ContextInputAccessError,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.enums import (
    ContextAssociationType,
    ContextEvaluationStatus,
    ContextualGapType,
)
from zovrake_motor.intelligent_analysis.context_evaluation_engine.governance import (
    EXPECTED_CONTEXT_ASSOCIATION_TYPES,
    EXPECTED_CONTEXTUAL_GAP_TYPES,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine import (
    EvidenceAnalysisBuilderEngine,
    EvidenceAnalysisRequest,
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


def _build_full_analysis_bundle(*, process_id=None, extra_providers=None, extra_commercial=None):
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
    requirement_context = {}
    if definitive_catalog.get("models"):
        requirement_context = dict(definitive_catalog["models"][0].get("inherited_context", {}))
    return (
        eae_result.catalog,
        cee_result.catalog,
        rae_result.catalog,
        definitive_catalog,
        requirement_context,
        process_id,
    )


class TestContextEvaluationBuilderEngine:
    def test_engine_initializes_with_one_evaluator(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_evaluates_context_from_full_analysis_bundle(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle()
        )

        result = engine.evaluate(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert result.consistency_catalog_preserved is True
        assert result.risk_catalog_preserved is True
        assert result.definitive_catalog_preserved is True
        assert result.requirement_context_preserved is True
        assert result.status in (
            ContextEvaluationStatus.EVALUATED,
            ContextEvaluationStatus.PARTIAL,
        )
        assert result.catalog.explanation_generation_engine_prepared is True
        assert len(result.catalog.profiles) >= 1

    def test_preserves_all_inputs_without_modification(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle()
        )
        evidence_snapshot = evidence_catalog.to_dict()
        consistency_snapshot = consistency_catalog.to_dict()
        risk_snapshot = risk_catalog.to_dict()
        definitive_snapshot = str(definitive_catalog)
        context_snapshot = str(requirement_context)

        engine.evaluate(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_snapshot
        assert consistency_catalog.to_dict() == consistency_snapshot
        assert risk_catalog.to_dict() == risk_snapshot
        assert str(definitive_catalog) == definitive_snapshot
        assert str(requirement_context) == context_snapshot

    def test_relates_context_with_evidence_and_detects_gaps(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle(
                extra_providers=["PROV-001", "PROV-002"],
                extra_commercial={"Precio": 1000, "Material": "Acero"},
            )
        )

        result = engine.evaluate(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        profile = result.catalog.profiles[0]
        for association in profile.associations:
            assert association.association_type.value in EXPECTED_CONTEXT_ASSOCIATION_TYPES
            assert association.traceability_ref.definitive_model_id
        for gap in profile.contextual_gaps:
            assert gap.description
            assert gap.gap_type.value in EXPECTED_CONTEXTUAL_GAP_TYPES

    def test_context_associations_remain_traceable(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle()
        )

        result = engine.evaluate(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        profile = result.catalog.profiles[0]
        if profile.associations:
            trace = profile.associations[0].traceability_ref
            assert trace.group_id
            assert trace.document_id
            assert trace.definitive_model_id

    def test_detects_contextual_gaps_without_completing_data(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle()
        )

        result = engine.evaluate(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        profile = result.catalog.profiles[0]
        assert result.contextual_gaps_count == len(profile.contextual_gaps)

    def test_rejects_invalid_input_bundle(self):
        engine = ContextEvaluationBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(ContextInputAccessError):
            engine.evaluate(
                ContextEvaluationRequest(
                    process_id=process_id,
                    evidence_catalog={"catalog_id": "invalid"},
                    consistency_catalog={"catalog_id": "invalid"},
                    risk_catalog={"catalog_id": "invalid"},
                    definitive_catalog={"catalog_id": "invalid"},
                ),
            )


class TestContextEvaluationIntegration:
    def test_service_evaluates_context_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle()
        )

        result = service.evaluate_context(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        assert result.definitive_catalog_preserved is True
        assert service.context_evaluation_engine is not None
        assert service.context_evaluation_engine.registry.count() == 1

    def test_pipeline_phase_follows_risk_analysis(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.ANALISIS_RIESGOS) < phases.index(
            IntelligentAnalysisPhase.EVALUACION_CONTEXTO,
        )
        assert (
            IntelligentAnalysisPipeline.context_evaluation_phase()
            == IntelligentAnalysisPhase.EVALUACION_CONTEXTO
        )

    def test_states_and_events_during_context_evaluation(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle(extra_providers=["PROV-001"])
        )

        service.evaluate_context(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                definitive_catalog=definitive_catalog,
                requirement_context=requirement_context,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cxee(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().context_evaluation_engine
        assert settings.enabled is True
        assert settings.organized_context_evaluator_enabled is True
        assert settings.explanation_generation_engine_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module(
            "zovrake_motor.intelligent_analysis.context_evaluation_engine",
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

    def test_copy_of_inputs_does_not_affect_original_after_evaluation(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, definitive_catalog, requirement_context, process_id = (
            _build_full_analysis_bundle(extra_providers=["PROV-001"])
        )
        evidence_copy = copy.deepcopy(evidence_catalog)
        consistency_copy = copy.deepcopy(consistency_catalog)
        risk_copy = copy.deepcopy(risk_catalog)
        definitive_copy = copy.deepcopy(definitive_catalog)
        context_copy = copy.deepcopy(requirement_context)

        service.evaluate_context(
            ContextEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_copy,
                consistency_catalog=consistency_copy,
                risk_catalog=risk_copy,
                definitive_catalog=definitive_copy,
                requirement_context=context_copy,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_copy.to_dict()
        assert consistency_catalog.to_dict() == consistency_copy.to_dict()
        assert risk_catalog.to_dict() == risk_copy.to_dict()
        assert str(definitive_catalog) == str(definitive_copy)
        assert str(requirement_context) == str(context_copy)

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

        assert cxee_result.evidence_catalog_preserved is True
        assert cxee_result.consistency_catalog_preserved is True
        assert cxee_result.risk_catalog_preserved is True
        assert cxee_result.catalog.explanation_generation_engine_prepared is True
        if cxee_result.catalog.profiles:
            profile = cxee_result.catalog.profiles[0]
            assert profile.context_elements_evaluated >= 0
            if profile.associations:
                assert profile.associations[0].association_type in (
                    ContextAssociationType.ALIGNMENT,
                    ContextAssociationType.PARTIAL_ALIGNMENT,
                    ContextAssociationType.LIMITATION,
                    ContextAssociationType.GAP,
                )
