"""
Punto de entrada de certificación del Módulo de Clasificación Inteligente.

Implementación 3.11 — Cierre oficial del Prompt Maestro 5.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.classification_checker import ClassificationModuleCertificationChecker


def main() -> int:
    checks = ClassificationModuleCertificationChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total

    print("=" * 60)
    print("CERTIFICACIÓN — MÓDULO DE CLASIFICACIÓN INTELIGENTE")
    print("Implementación 3.11 — Prompt Maestro 5")
    print("=" * 60)
    print(f"Versión del Motor: {__version__}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Certificación del módulo: {'APROBADA' if approved else 'RECHAZADA'}")
    print(f"Preparado para Prompt Maestro 6: {'SÍ' if approved else 'NO'}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "3.11",
                "prompt_maestro": "5",
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
