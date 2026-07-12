"""Pruebas de cierre formal del Prompt Maestro 5 — Implementación 3.12."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zovrake_motor import ClassificationService, __version__
from zovrake_motor.certification import CoreCertificationChecker
from zovrake_motor.certification.classification_closure_checker import ClassificationModuleClosureChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.classification.governance import (
    PROMPT_MAESTRO_5_STATUS,
    closure_snapshot,
    frozen_component_names,
)

CLASSIFICATION_ROOT = Path(__file__).resolve().parents[2] / "zovrake_motor" / "classification"


class TestClassificationModuleClosure:
    def test_closure_certification_passes(self):
        checks = ClassificationModuleClosureChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_core_certification_declares_pm5_closed(self):
        report = CoreCertificationChecker().run()
        assert CertificationArea.CLASSIFICATION_MODULE_CLOSURE in {c.area for c in report.checks}
        assert report.prompt_maestro_5_closed

    def test_governance_declares_prompt_maestro_5_closed(self):
        snapshot = closure_snapshot()
        assert snapshot["status"] == PROMPT_MAESTRO_5_STATUS
        assert snapshot["prompt_maestro"] == "5"
        assert snapshot["next_prompt_maestro"] == "6"
        assert len(snapshot["frozen_components"]) == 9

    def test_frozen_components_match_registry(self):
        service = ClassificationService()
        service.initialize()
        for name in frozen_component_names():
            component = service.component_registry.get(name)
            assert component is not None
            assert component.is_ready()

    def test_closure_documentation_exists(self):
        for filename in ("CLOSURE.md", "OUTPUT_CONTRACT.md", "CERTIFICATION.md", "ARCHITECTURE.md"):
            assert (CLASSIFICATION_ROOT / filename).is_file()

    def test_version_reflects_closure_release(self):
        assert __version__ == "8.12.0"

    def test_output_contract_metadata_complete(self):
        contract = closure_snapshot()["output_contract"]
        assert contract["name"] == "ComparativeDomainModelCatalog"
        assert contract["version"] == "1.0"
        assert "pm6_output_contract" in contract["required_catalog_fields"]
        assert "traceability" in contract["required_model_fields"]

    def test_architectural_boundaries_declared(self):
        boundaries = closure_snapshot()["architectural_boundaries"]
        modules = {item["module"] for item in boundaries}
        assert modules == {"comprehension", "classification", "comparative_tables"}
