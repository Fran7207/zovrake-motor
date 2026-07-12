"""Pruebas de cierre formal del Prompt Maestro 7 — Implementación 7.10."""

from __future__ import annotations

import json
from pathlib import Path

from zovrake_motor import IntelligentAnalysisService, __version__
from zovrake_motor.certification import CoreCertificationChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.certification.intelligent_analysis_closure_checker import (
    IntelligentAnalysisModuleClosureChecker,
)
from zovrake_motor.intelligent_analysis.governance import (
    PROMPT_MAESTRO_7_STATUS,
    closure_snapshot,
    frozen_component_names,
)

INTELLIGENT_ANALYSIS_ROOT = Path(__file__).resolve().parents[2] / "zovrake_motor" / "intelligent_analysis"


class TestIntelligentAnalysisModuleClosure:
    def test_closure_certification_passes(self):
        checks = IntelligentAnalysisModuleClosureChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_core_certification_declares_pm7_closed(self):
        report = CoreCertificationChecker().run()
        assert CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE in {c.area for c in report.checks}
        assert report.prompt_maestro_7_closed

    def test_governance_declares_prompt_maestro_7_closed(self):
        snapshot = closure_snapshot()
        assert snapshot["status"] == PROMPT_MAESTRO_7_STATUS
        assert snapshot["prompt_maestro"] == "7"
        assert snapshot["next_prompt_maestro"] == "8"
        assert len(snapshot["frozen_components"]) == 7

    def test_frozen_components_match_registry(self):
        service = IntelligentAnalysisService()
        service.initialize()
        for name in frozen_component_names():
            component = service.component_registry.get(name)
            assert component is not None
            assert component.is_ready()

    def test_closure_documentation_exists(self):
        for filename in ("CLOSURE.md", "OUTPUT_CONTRACT.md", "CERTIFICATION.md", "ARCHITECTURE.md"):
            assert (INTELLIGENT_ANALYSIS_ROOT / filename).is_file()

    def test_version_reflects_closure_release(self):
        assert __version__ == "8.12.0"

    def test_output_contract_metadata_complete(self):
        contract = closure_snapshot()["output_contract"]
        assert contract["name"] == "IntelligentAnalysisResultCatalog"
        assert contract["version"] == "1.0"
        assert "source_evidence_catalog_id" in contract["required_catalog_fields"]
        assert "document_traceability" in contract["required_result_fields"]

    def test_architectural_boundaries_declared(self):
        boundaries = closure_snapshot()["architectural_boundaries"]
        modules = {item["module"] for item in boundaries}
        assert modules == {"comparative_tables", "intelligent_analysis", "processing"}

    def test_xai_principles_declared(self):
        xai = closure_snapshot()["xai_principles"]
        assert xai["explainable_recommendations"] is True
        assert xai["traceable_explanations"] is True
        assert xai["evidence_backed_conclusions"] is True
