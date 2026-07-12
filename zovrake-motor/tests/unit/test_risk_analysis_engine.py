"""Pruebas del Risk Analysis Engine — Implementación 7.4."""

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
from zovrake_motor.intelligent_analysis.evidence_analysis_engine import (
    EvidenceAnalysisBuilderEngine,
    EvidenceAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine import (
    AnalysisInputAccessError,
    RiskAnalysisBuilderEngine,
    RiskAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.enums import (
    RiskAnalysisStatus,
    RiskCategory,
    RiskStatus,
)
from zovrake_motor.intelligent_analysis.risk_analysis_engine.governance import (
    EXPECTED_RISK_CATEGORIES,
)
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_validation_framework import build_definitive_catalog


def _build_analysis_bundle(*, process_id=None, extra_providers=None, extra_commercial=None):
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
    return eae_result.catalog, cee_result.catalog, process_id


class TestRiskAnalysisBuilderEngine:
    def test_engine_initializes_with_one_analyzer(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_analyzes_risks_from_evidence_and_consistency(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle()

        result = engine.analyze(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert result.consistency_catalog_preserved is True
        assert result.source_data_preserved is True
        assert result.status in (
            RiskAnalysisStatus.ANALYZED,
            RiskAnalysisStatus.PARTIAL,
        )
        assert result.catalog.context_evaluation_engine_prepared is True
        assert len(result.catalog.profiles) >= 1

    def test_preserves_input_catalogs_without_modification(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle()
        evidence_snapshot = evidence_catalog.to_dict()
        consistency_snapshot = consistency_catalog.to_dict()

        engine.analyze(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_snapshot
        assert consistency_catalog.to_dict() == consistency_snapshot

    def test_identifies_and_classifies_risks_without_resolving(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle(
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 1000, "Material": "Acero"},
        )

        result = engine.analyze(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        assert result.risks_count >= 0
        profile = result.catalog.profiles[0]
        for risk in profile.risks:
            assert risk.description
            assert risk.risk_category.value in EXPECTED_RISK_CATEGORIES
            assert risk.risk_status == RiskStatus.IDENTIFIED

    def test_risks_remain_linked_to_evidence(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle()

        result = engine.analyze(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        if profile.risks:
            risk = profile.risks[0]
            trace = risk.traceability_ref
            assert trace.definitive_model_id
            assert trace.group_id
            assert trace.document_id
            assert (
                risk.associated_evidence_ids
                or risk.associated_inconsistency_ids
                or risk.associated_missing_evidence_ids
                or trace.missing_evidence_id
                or trace.inconsistency_id
            )

    def test_classifies_risks_by_category(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle()

        result = engine.analyze(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        categories = {risk.risk_category for risk in profile.risks}
        if categories:
            assert any(cat in categories for cat in (
                RiskCategory.DOCUMENTATION,
                RiskCategory.INFORMATION,
                RiskCategory.CONSISTENCY,
                RiskCategory.COMMERCIAL,
                RiskCategory.TECHNICAL,
            ))

    def test_rejects_invalid_input_bundle(self):
        engine = RiskAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(AnalysisInputAccessError):
            engine.analyze(
                RiskAnalysisRequest(
                    process_id=process_id,
                    evidence_catalog={"catalog_id": "invalid"},
                    consistency_catalog={"catalog_id": "invalid"},
                ),
            )


class TestRiskAnalysisIntegration:
    def test_service_analyzes_risks_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle()

        result = service.analyze_risks(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        assert result.evidence_catalog_preserved is True
        assert result.consistency_catalog_preserved is True
        assert service.risk_analysis_engine is not None
        assert service.risk_analysis_engine.registry.count() == 1

    def test_pipeline_phase_follows_consistency_evaluation(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.EVALUACION_CONSISTENCIA) < phases.index(
            IntelligentAnalysisPhase.ANALISIS_RIESGOS,
        )
        assert (
            IntelligentAnalysisPipeline.risk_analysis_phase()
            == IntelligentAnalysisPhase.ANALISIS_RIESGOS
        )

    def test_states_and_events_during_risk_analysis(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle(
            extra_providers=["PROV-001"],
        )

        service.analyze_risks(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_catalog,
                consistency_catalog=consistency_catalog,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_rae(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().risk_analysis_engine
        assert settings.enabled is True
        assert settings.organized_evidence_risk_analyzer_enabled is True
        assert settings.context_evaluation_engine_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module("zovrake_motor.intelligent_analysis.risk_analysis_engine")
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

    def test_copy_of_input_catalogs_does_not_affect_original_after_analysis(self):
        service = IntelligentAnalysisService()
        service.initialize()
        evidence_catalog, consistency_catalog, process_id = _build_analysis_bundle(
            extra_providers=["PROV-001"],
        )
        evidence_copy = copy.deepcopy(evidence_catalog)
        consistency_copy = copy.deepcopy(consistency_catalog)

        service.analyze_risks(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=evidence_copy,
                consistency_catalog=consistency_copy,
            ),
        )

        assert evidence_catalog.to_dict() == evidence_copy.to_dict()
        assert consistency_catalog.to_dict() == consistency_copy.to_dict()

    def test_eae_cee_rae_chain_preserves_data(self):
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
        evidence_snapshot = eae_result.catalog.to_dict()

        cee_result = service.evaluate_consistency(
            ConsistencyEvaluationRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
            ),
        )
        consistency_snapshot = cee_result.catalog.to_dict()

        rae_result = service.analyze_risks(
            RiskAnalysisRequest(
                process_id=process_id,
                evidence_catalog=eae_result.catalog,
                consistency_catalog=cee_result.catalog,
            ),
        )

        assert eae_result.catalog.to_dict() == evidence_snapshot
        assert cee_result.catalog.to_dict() == consistency_snapshot
        assert rae_result.evidence_catalog_preserved is True
        assert rae_result.consistency_catalog_preserved is True
        assert rae_result.catalog.context_evaluation_engine_prepared is True
