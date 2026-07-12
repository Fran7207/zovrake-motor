"""
Punto de entrada de certificación del Módulo de Razonamiento Inteligente.

Implementación 7.9 — Integración y certificación del Prompt Maestro 7.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.intelligent_analysis_checker import (
    IntelligentAnalysisModuleCertificationChecker,
)


def main() -> int:
    checks = IntelligentAnalysisModuleCertificationChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total

    print("=" * 60)
    print("CERTIFICACIÓN — MÓDULO DE RAZONAMIENTO INTELIGENTE")
    print("Implementación 7.9 — Prompt Maestro 7")
    print("=" * 60)
    print(f"Versión del Motor: {__version__}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Certificación del módulo: {'APROBADA' if approved else 'RECHAZADA'}")
    print(f"Preparado para cierre oficial (7.10): {'SÍ' if approved else 'NO'}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "7.9",
                "prompt_maestro": "7",
                "passed": approved,
                "total_checks": total,
                "passed_checks": passed,
                "checks": [check.to_dict() for check in checks],
            },
            indent=2,
            ensure_ascii=False,
        ),
    )
    return 0 if approved else 1


if __name__ == "__main__":
    sys.exit(main())
