"""Pruebas del Evidence Analysis Engine — Implementación 7.2."""

from __future__ import annotations

import copy
import importlib
import pkgutil
from pathlib import Path
from uuid import uuid4

import pytest

from zovrake_motor import IntelligentAnalysisService
from zovrake_motor.intelligent_analysis.evidence_analysis_engine import (
    DefinitiveCatalogAccessError,
    EvidenceAnalysisBuilderEngine,
    EvidenceAnalysisRequest,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import (
    EvidenceAnalysisStatus,
    EvidenceCategory,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.governance import (
    EXPECTED_EVIDENCE_CATEGORIES,
)
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisPhase
from zovrake_motor.intelligent_analysis.pipeline import IntelligentAnalysisPipeline
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager
from zovrake_motor.states import MotorState, StateManager
from tests.unit.test_comparative_validation_framework import build_definitive_catalog


class TestEvidenceAnalysisBuilderEngine:
    def test_engine_initializes_with_one_analyzer(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()

        assert engine.is_ready()
        assert engine.registry.count() == 1

    def test_analyzes_definitive_catalog_and_identifies_evidence(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 1000},
        )

        result = engine.analyze(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.evidence_records_count > 0
        assert result.definitive_catalog_preserved is True
        assert result.source_data_preserved is True
        assert result.status in (
            EvidenceAnalysisStatus.ANALYZED,
            EvidenceAnalysisStatus.PARTIAL,
        )
        assert result.catalog.consistency_evaluation_engine_prepared is True
        assert len(result.catalog.profiles) >= 1

    def test_preserves_definitive_catalog_without_modification(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )
        snapshot_before = str(definitive_catalog)

        engine.analyze(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert str(definitive_catalog) == snapshot_before

    def test_detects_missing_information_without_completing_data(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
        )

        result = engine.analyze(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.missing_evidence_records_count >= 0
        if result.catalog.profiles:
            profile = result.catalog.profiles[0]
            for missing in profile.missing_evidence_records:
                assert missing.reason
                assert missing.evidence_category.value in EXPECTED_EVIDENCE_CATEGORIES

    def test_evidence_records_remain_traceable(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 1000},
        )

        result = engine.analyze(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        profile = result.catalog.profiles[0]
        assert profile.evidence_records
        record = profile.evidence_records[0]
        trace = record.traceability_ref
        assert trace.document_id == definitive_catalog["document_id"]
        assert trace.definitive_model_id
        assert trace.group_id
        assert trace.source_field

    def test_organizes_evidence_by_category(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001"],
            extra_commercial={"Precio": 1000, "Entrega": "15 días"},
        )

        result = engine.analyze(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        categories = {
            record.evidence_category
            for profile in result.catalog.profiles
            for record in profile.evidence_records
        }
        assert EvidenceCategory.COMMERCIAL_INFORMATION in categories or EvidenceCategory.METADATA in categories

    def test_rejects_invalid_definitive_catalog(self):
        engine = EvidenceAnalysisBuilderEngine()
        engine.initialize()
        process_id = uuid4()

        with pytest.raises(DefinitiveCatalogAccessError):
            engine.analyze(
                EvidenceAnalysisRequest(
                    process_id=process_id,
                    definitive_catalog={"catalog_id": "invalid"},
                ),
            )


class TestEvidenceAnalysisIntegration:
    def test_service_analyzes_evidence_through_pipeline(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(
            process_id=process_id,
            extra_providers=["PROV-001", "PROV-002"],
            extra_commercial={"Precio": 2500},
        )

        result = service.analyze_evidence(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        assert result.evidence_records_count > 0
        assert result.definitive_catalog_preserved is True
        assert service.evidence_analysis_engine is not None
        assert service.evidence_analysis_engine.registry.count() == 1

    def test_pipeline_phase_is_first_functional_stage(self):
        phases = IntelligentAnalysisPipeline.ordered_phases()
        assert phases.index(IntelligentAnalysisPhase.CONSUMO_MODELO_COMPARATIVO_DEFINITIVO) < phases.index(
            IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS,
        )
        assert IntelligentAnalysisPipeline.evidence_analysis_phase() == IntelligentAnalysisPhase.ANALISIS_EVIDENCIAS

    def test_states_and_events_during_evidence_analysis(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(process_id=process_id, extra_providers=["PROV-001"])

        service.analyze_evidence(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=definitive_catalog,
            ),
        )

        state = state_manager.get_process(process_id)
        assert state is not None
        assert state.current_state == MotorState.PROCESAMIENTO_COMPLETADO
        assert event_manager.count() >= 2

    def test_module_ready_count_includes_eae(self):
        service = IntelligentAnalysisService()
        service.initialize()
        assert service.component_registry.ready_count() == 11

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.intelligent_analysis().evidence_analysis_engine
        assert settings.enabled is True
        assert settings.definitive_model_evidence_analyzer_enabled is True
        assert settings.consistency_evaluation_engine_prepared is True

    def test_no_direct_imports_from_comparative_tables_module(self):
        package = importlib.import_module("zovrake_motor.intelligent_analysis.evidence_analysis_engine")
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

    def test_copy_of_catalog_does_not_affect_original_after_analysis(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()
        definitive_catalog, _ = build_definitive_catalog(process_id=process_id, extra_providers=["PROV-001"])
        working_copy = copy.deepcopy(definitive_catalog)

        service.analyze_evidence(
            EvidenceAnalysisRequest(
                process_id=process_id,
                definitive_catalog=working_copy,
            ),
        )

        assert str(definitive_catalog) == str(working_copy)
