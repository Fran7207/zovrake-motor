"""Pruebas de certificación arquitectónica — Implementación 1.10."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from zovrake_motor import __version__
from zovrake_motor.certification import CoreCertificationChecker, build_certified_stack
from zovrake_motor.certification.enums import CertificationArea

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestCoreCertification:
    def test_certification_report_passes(self):
        report = CoreCertificationChecker().run()
        assert report.passed, json.dumps(
            [c.to_dict() for c in report.checks if not c.passed],
            indent=2,
        )

    def test_all_areas_covered(self):
        report = CoreCertificationChecker().run()
        areas = {check.area for check in report.checks}
        expected = set(CertificationArea)
        assert expected.issubset(areas)

    def test_certified_prompt_maestro_4_complete(self):
        report = CoreCertificationChecker().run()
        assert report.certified_prompt_maestro_4_complete

    def test_prompt_maestro_5_closed(self):
        report = CoreCertificationChecker().run()
        assert report.prompt_maestro_5_closed

    def test_certified_prompt_maestro_6_complete(self):
        report = CoreCertificationChecker().run()
        assert report.certified_prompt_maestro_6_complete

    def test_minimum_check_count(self):
        report = CoreCertificationChecker().run()
        assert report.total_checks >= 95

    def test_certify_script_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "certify.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "APROBADA" in result.stdout

    def test_build_certified_stack_integration(self):
        coordinator, config, state_manager, event_manager = build_certified_stack()
        assert coordinator.is_ready()
        assert config.service_name() == "zovrake-motor"
        assert state_manager.count() == 0
        assert event_manager.count() == 0

        result = coordinator.coordinate(metadata={"codigo_req": "CERT-INTEGRATION"})
        assert result.success
        assert "process_state" in result.metadata
        assert "process_events" in result.metadata
        assert "internal_pipeline" in result.metadata

    def test_version_is_certified_release(self):
        assert __version__ == "9.4.0"
