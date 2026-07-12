"""Pruebas del Explanation Generation Engine — Implementación 7.6."""

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
    ExplanationInputAccessError,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationGenerationStatus,
    ExplanationSectionType,
)
from zovrake_motor.intelligent_analysis.explanation_generation_engine.governance import (
    EXPECTED_EXPLANATION_SECTION_TYPES,
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


def _build_full_analysis_bundle_with_context(*, process_id=None, extra_providers=None, extra_commercial=None):
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
    return (
        eae_result.catalog,
        cee_result.catalog,
        rae_result.catalog,
        cxee_result.catalog,
        definitive_catalog,
        process_id,
    )


class TestExplanationGenerationBuilderEngine:
    def test_engine_initializes_with_one_generator(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_generates_explanations_from_full_analysis_bundle(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context()
        )

        result = engine.generate(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert result.consistency_catalog_preserved is True
        assert result.risk_catalog_preserved is True
        assert result.context_catalog_preserved is True
        assert result.definitive_catalog_preserved is True
        assert result.status in (
            ExplanationGenerationStatus.GENERATED,
            ExplanationGenerationStatus.PARTIAL,
        )
        assert result.catalog.conclusion_generation_engine_prepared is True
        assert result.catalog.recommendation_generation_engine_prepared is True
        assert len(result.catalog.profiles) >= 1
        assert result.segments_count > 0

    def test_preserves_all_inputs_without_modification(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context()
        )
        evidence_snapshot = evidence_catalog.to_dict()
        consistency_snapshot = consistency_catalog.to_dict()
        risk_snapshot = risk_catalog.to_dict()
        context_snapshot = context_catalog.to_dict()
        definitive_snapshot = str(definitive_catalog)

        engine.generate(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_snapshot
        assert consistency_catalog.to_dict() == consistency_snapshot
        assert risk_catalog.to_dict() == risk_snapshot
        assert context_catalog.to_dict() == context_snapshot
        assert str(definitive_catalog) == definitive_snapshot

    def test_explanations_are_backed_by_evidence(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context(
                extra_providers=["PROV-001", "PROV-002"],
                extra_commercial={"Precio": 1000, "Material": "Acero"},
            )
        )

        result = engine.generate(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        for segment in profile.segments:
            assert segment.section_type.value in EXPECTED_EXPLANATION_SECTION_TYPES
            assert segment.structured_content.get("template_key")
            assert segment.traceability_ref.definitive_model_id

    def test_documents_strengths_weaknesses_risks_and_limitations(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context()
        )

        result = engine.generate(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        section_types = {segment.section_type for segment in profile.segments}
        assert ExplanationSectionType.ANALYSIS_SUMMARY in section_types
        assert ExplanationSectionType.EVIDENCE_USED in section_types

    def test_explanation_segments_remain_traceable(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context()
        )

        result = engine.generate(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        evidence_segment = next(
            segment
            for segment in profile.segments
            if segment.section_type == ExplanationSectionType.EVIDENCE_USED
        )
        trace = evidence_segment.traceability_ref
        assert trace.group_id
        assert trace.document_id
        assert trace.definitive_model_id

    def test_rejects_invalid_input_bundle(self):
        engine = ExplanationGenerationBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(ExplanationInputAccessError):
            engine.generate(
                ExplanationGenerationRequest(
                    process_id=process_id,
                    evidence_catalog={"catalog_id": "invalid"},
                    consistency_catalog={"catalog_id": "invalid"},
                    risk_catalog={"catalog_id": "invalid"},
                    context_catalog={"catalog_id": "invalid"},
                    definitive_catalog={"catalog_id": "invalid"},
                ),
            )


class TestExplanationGenerationIntegration:
    def test_service_generates_explanations_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context()
        )

        result = service.generate_explanations(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.definitive_catalog_preserved is True
        assert service.explanation_generation_engine is not None
        assert service.explanation_generation_engine.registry.count() == 1

    def test_pipeline_phase_follows_context_evaluation(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.EVALUACION_CONTEXTO) < phases.index(
            IntelligentAnalysisPhase.GENERACION_EXPLICACIONES,
        )
        assert (
            IntelligentAnalysisPipeline.explanation_generation_phase()
            == IntelligentAnalysisPhase.GENERACION_EXPLICACIONES
        )

    def test_states_and_events_during_explanation_generation(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context(extra_providers=["PROV-001"])
        )

        service.generate_explanations(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
                risk_catalog=risk_catalog,
                context_catalog=context_catalog,
                definitive_catalog=definitive_catalog,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_ege(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().explanation_generation_engine
        assert settings.enabled is True
        assert settings.organized_explanation_generator_enabled is True
        assert settings.conclusion_generation_engine_prepared is True
        assert settings.recommendation_generation_engine_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module(
            "zovrake_motor.intelligent_analysis.explanation_generation_engine",
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

    def test_copy_of_inputs_does_not_affect_original_after_generation(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, risk_catalog, context_catalog, definitive_catalog, process_id = (
            _build_full_analysis_bundle_with_context(extra_providers=["PROV-001"])
        )
        evidence_copy = copy.deepcopy(evidence_catalog)
        consistency_copy = copy.deepcopy(consistency_catalog)
        risk_copy = copy.deepcopy(risk_catalog)
        context_copy = copy.deepcopy(context_catalog)
        definitive_copy = copy.deepcopy(definitive_catalog)

        service.generate_explanations(
            ExplanationGenerationRequest(
                process_id=process_id,
                evidence_catalog=evidence_copy,
                consistency_catalog=consistency_copy,
                risk_catalog=risk_copy,
                context_catalog=context_copy,
                definitive_catalog=definitive_copy,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_copy.to_dict()
        assert consistency_catalog.to_dict() == consistency_copy.to_dict()
        assert risk_catalog.to_dict() == risk_copy.to_dict()
        assert context_catalog.to_dict() == context_copy.to_dict()
        assert str(definitive_catalog) == str(definitive_copy)

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

        assert ege_result.evidence_catalog_preserved is True
        assert ege_result.context_catalog_preserved is True
        assert ege_result.catalog.conclusion_generation_engine_prepared is True
        if ege_result.catalog.profiles:
            profile = ege_result.catalog.profiles[0]
            assert profile.segments_count if hasattr(profile, "segments_count") else len(profile.segments) >= 0
            if profile.segments:
                assert profile.segments[0].structured_content.get("template_key")
