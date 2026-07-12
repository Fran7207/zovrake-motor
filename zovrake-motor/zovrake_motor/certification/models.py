"""Modelos del reporte de certificación arquitectónica."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from zovrake_motor.certification.enums import CertificationArea, CertificationStatus


@dataclass(frozen=True)
class CertificationCheck:
    """Resultado de una verificación individual."""

    area: CertificationArea
    name: str
    status: CertificationStatus
    message: str

    @property
    def passed(self) -> bool:
        return self.status == CertificationStatus.PASSED

    def to_dict(self) -> dict[str, Any]:
        return {
            "area": self.area.value,
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }


@dataclass
class CertificationReport:
    """Reporte consolidado de certificación del núcleo."""

    motor_version: str
    prompt_maestro: str = "6"
    implementation: str = "4.11"
    checks: list[CertificationCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for check in self.checks if check.passed)

    @property
    def failed_checks(self) -> int:
        return self.total_checks - self.passed_checks

    @property
    def certified_for_prompt_maestro_4(self) -> bool:
        pm4_checks = [
            check for check in self.checks if check.area == CertificationArea.PROMPT_MAESTRO_4
        ]
        return self.passed and all(check.passed for check in pm4_checks)

    @property
    def certified_prompt_maestro_4_complete(self) -> bool:
        comprehension_checks = [
            check for check in self.checks if check.area == CertificationArea.COMPREHENSION_MODULE
        ]
        return (
            self.certified_for_prompt_maestro_4
            and len(comprehension_checks) > 0
            and all(check.passed for check in comprehension_checks)
        )

    @property
    def certified_for_prompt_maestro_5(self) -> bool:
        pm5_checks = [
            check for check in self.checks if check.area == CertificationArea.PROMPT_MAESTRO_5
        ]
        return self.passed and all(check.passed for check in pm5_checks)

    @property
    def certified_prompt_maestro_5_complete(self) -> bool:
        classification_checks = [
            check for check in self.checks if check.area == CertificationArea.CLASSIFICATION_MODULE
        ]
        return (
            self.certified_prompt_maestro_4_complete
            and len(classification_checks) > 0
            and all(check.passed for check in classification_checks)
        )

    @property
    def prompt_maestro_5_closed(self) -> bool:
        closure_checks = [
            check for check in self.checks if check.area == CertificationArea.CLASSIFICATION_MODULE_CLOSURE
        ]
        return (
            self.certified_prompt_maestro_5_complete
            and len(closure_checks) > 0
            and all(check.passed for check in closure_checks)
        )

    @property
    def certified_for_prompt_maestro_6(self) -> bool:
        pm6_checks = [
            check for check in self.checks if check.area == CertificationArea.PROMPT_MAESTRO_6
        ]
        return self.passed and all(check.passed for check in pm6_checks)

    @property
    def certified_prompt_maestro_6_complete(self) -> bool:
        comparative_checks = [
            check for check in self.checks if check.area == CertificationArea.COMPARATIVE_TABLES_MODULE
        ]
        return (
            self.certified_prompt_maestro_5_complete
            and len(comparative_checks) > 0
            and all(check.passed for check in comparative_checks)
        )

    @property
    def certified_for_prompt_maestro_7(self) -> bool:
        pm7_checks = [
            check for check in self.checks if check.area == CertificationArea.PROMPT_MAESTRO_7
        ]
        return self.passed and all(check.passed for check in pm7_checks)

    @property
    def certified_prompt_maestro_7_complete(self) -> bool:
        intelligent_analysis_checks = [
            check for check in self.checks if check.area == CertificationArea.INTELLIGENT_ANALYSIS_MODULE
        ]
        return (
            self.certified_prompt_maestro_6_complete
            and len(intelligent_analysis_checks) > 0
            and all(check.passed for check in intelligent_analysis_checks)
        )

    @property
    def prompt_maestro_7_closed(self) -> bool:
        closure_checks = [
            check for check in self.checks
            if check.area == CertificationArea.INTELLIGENT_ANALYSIS_MODULE_CLOSURE
        ]
        return (
            self.certified_prompt_maestro_7_complete
            and len(closure_checks) > 0
            and all(check.passed for check in closure_checks)
        )

    @property
    def prompt_maestro_8_closed(self) -> bool:
        closure_checks = [
            check for check in self.checks
            if check.area == CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE
        ]
        platform_checks = [
            check for check in self.checks
            if check.area == CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM
        ]
        return (
            len(platform_checks) > 0
            and all(check.passed for check in platform_checks)
            and len(closure_checks) > 0
            and all(check.passed for check in closure_checks)
        )

    def summary_by_area(self) -> dict[str, dict[str, int]]:
        summary: dict[str, dict[str, int]] = {}
        for check in self.checks:
            area = check.area.value
            if area not in summary:
                summary[area] = {"passed": 0, "failed": 0, "total": 0}
            summary[area]["total"] += 1
            if check.passed:
                summary[area]["passed"] += 1
            else:
                summary[area]["failed"] += 1
        return summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "motor_version": self.motor_version,
            "prompt_maestro": self.prompt_maestro,
            "implementation": self.implementation,
            "passed": self.passed,
            "certified_for_prompt_maestro_4": self.certified_for_prompt_maestro_4,
            "certified_prompt_maestro_4_complete": self.certified_prompt_maestro_4_complete,
            "certified_for_prompt_maestro_5": self.certified_for_prompt_maestro_5,
            "certified_prompt_maestro_5_complete": self.certified_prompt_maestro_5_complete,
            "prompt_maestro_5_closed": self.prompt_maestro_5_closed,
            "certified_for_prompt_maestro_6": self.certified_for_prompt_maestro_6,
            "certified_prompt_maestro_6_complete": self.certified_prompt_maestro_6_complete,
            "certified_for_prompt_maestro_7": self.certified_for_prompt_maestro_7,
            "certified_prompt_maestro_7_complete": self.certified_prompt_maestro_7_complete,
            "prompt_maestro_7_closed": self.prompt_maestro_7_closed,
            "prompt_maestro_8_closed": self.prompt_maestro_8_closed,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "summary_by_area": self.summary_by_area(),
            "checks": [check.to_dict() for check in self.checks],
        }
