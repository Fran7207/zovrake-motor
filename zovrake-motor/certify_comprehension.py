"""
Punto de entrada de certificación del Módulo de Comprensión Documental.

Implementación 2.10 — Cierre oficial del Prompt Maestro 4.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.comprehension_checker import ComprehensionModuleCertificationChecker


def main() -> int:
    checks = ComprehensionModuleCertificationChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total

    print("=" * 60)
    print("CERTIFICACIÓN — MÓDULO DE COMPRENSIÓN DOCUMENTAL")
    print("Implementación 2.10 — Prompt Maestro 4")
    print("=" * 60)
    print(f"Versión del Motor: {__version__}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Certificación del módulo: {'APROBADA' if approved else 'RECHAZADA'}")
    print(f"Preparado para Prompt Maestro 5: {'SÍ' if approved else 'NO'}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "2.10",
                "prompt_maestro": "4",
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
