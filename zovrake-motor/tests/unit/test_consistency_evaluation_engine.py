"""Pruebas del Consistency Evaluation Engine — Implementación 7.3."""

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
    EvidenceCatalogAccessError,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyEvaluationStatus,
    InconsistencyType,
    SufficiencyLevel,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.governance import (
    EXPECTED_CONSISTENCY_CRITERIA,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine import (
    EvidenceAnalysisBuilderEngine,
    EvidenceAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_validation_framework import build_definitive_catalog


def _build_evidence_catalog(*, process_id=None, extra_providers=None, extra_commercial=None):
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
    return eae_result.catalog, process_id


class TestConsistencyEvaluationBuilderEngine:
    def test_engine_initializes_with_one_evaluator(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_evaluates_evidence_catalog_and_detects_consistency(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, process_id = _build_evidence_catalog()

        result = engine.evaluate(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert result.source_data_preserved is True
        assert result.status in (
            ConsistencyEvaluationStatus.EVALUATED,
            ConsistencyEvaluationStatus.PARTIAL,
        )
        assert result.catalog.risk_analysis_engine_prepared is True
        assert len(result.catalog.profiles) >= 1
        assert result.catalog.profiles[0].criteria_evaluated

    def test_preserves_evidence_catalog_without_modification(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, process_id = _build_evidence_catalog()
        snapshot_before = evidence_catalog.to_dict()

        engine.evaluate(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        assert evidence_catalog.to_dict() == snapshot_before

    def test_detects_inconsistencies_without_correcting_data(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, process_id = _build_evidence_catalog(
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 1000, "Material": "Acero"},
        )

        result = engine.evaluate(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        for inconsistency in profile.inconsistencies:
            assert inconsistency.description
            assert inconsistency.inconsistency_type.value in (
                item.value for item in InconsistencyType
            )
            assert inconsistency.criterion.value in EXPECTED_CONSISTENCY_CRITERIA

    def test_assesses_sufficiency_for_reasoning(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, process_id = _build_evidence_catalog()

        result = engine.evaluate(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        sufficiency = profile.sufficiency
        assert sufficiency.sufficiency_level in (
            SufficiencyLevel.SUFFICIENT,
            SufficiencyLevel.PARTIAL,
            SufficiencyLevel.INSUFFICIENT,
        )
        assert sufficiency.reason
        assert result.sufficient_profiles_count + result.insufficient_profiles_count == len(
            result.catalog.profiles,
        )

    def test_inconsistencies_remain_traceable(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()
        evidence_catalog, process_id = _build_evidence_catalog()

        result = engine.evaluate(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        if profile.inconsistencies:
            trace = profile.inconsistencies[0].traceability_ref
            assert trace.definitive_model_id
            assert trace.group_id
            assert trace.document_id

    def test_rejects_invalid_evidence_catalog(self):
        engine = ConsistencyEvaluationBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(EvidenceCatalogAccessError):
            engine.evaluate(
                ConsistencyEvaluationRequest(
                    process_id=process_id,
                    evidence_catalog={"catalog_id": "invalid"},
                ),
            )


class TestConsistencyEvaluationIntegration:
    def test_service_evaluates_consistency_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, process_id = _build_evidence_catalog()

        result = service.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert service.consistency_evaluation_engine is not None
        assert service.consistency_evaluation_engine.registry.count() == 1

    def test_pipeline_phase_follows_evidence_analysis(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS) < phases.index(
            IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA,
        )
        assert (
            IntelligentAnalysisPipeline.consistency_evaluation_phase()
            == IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA
        )

    def test_states_and_events_during_consistency_evaluation(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        evidence_catalog, process_id = _build_evidence_catalog(extra_providers=["PROV-001"])

        service.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_cee(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().consistency_evaluation_engine
        assert settings.enabled is True
        assert settings.organized_evidence_evaluator_enabled is True
        assert settings.risk_analysis_engine_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module(
            "zovrake_motor.intelligent_analysis.consistency_evaluation_engine",
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

    def test_copy_of_evidence_catalog_does_not_affect_original_after_evaluation(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, process_id = _build_evidence_catalog(extra_providers=["PROV-001"])
        working_copy = copy.deepcopy(evidence_catalog)

        service.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=working_copy,
            ),
        )

        assert evidence_catalog.to_dict() == working_copy.to_dict()

    def test_eae_to_cee_chain_preserves_data(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 2500},
        )

        eae_result = service.analyze_evidence(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )
        catalog_snapshot = eae_result.catalog.to_dict()

        cee_result = service.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
            ),
        )

        assert eae_result.catalog.to_dict() == catalog_snapshot
        assert cee_result.evidence_catalog_preserved is True
        assert cee_result.catalog.risk_analysis_engine_prepared is True
