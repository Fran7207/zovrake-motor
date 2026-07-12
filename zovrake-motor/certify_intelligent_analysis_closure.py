"""
Punto de entrada del cierre formal del Prompt Maestro 7.

Implementación 7.10 — Gobierno arquitectónico del Módulo de Razonamiento Inteligente.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.intelligent_analysis_closure_checker import (
    IntelligentAnalysisModuleClosureChecker,
)
from zovrake_motor.intelligent_analysis.governance import closure_snapshot


def main() -> int:
    checks = IntelligentAnalysisModuleClosureChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total
    governance = closure_snapshot()

    print("=" * 60)
    print("CIERRE FORMAL — PROMPT MAESTRO 7")
    print("Módulo de Razonamiento Inteligente — Implementación 7.10")
    print("=" * 60)
    print(f"Versión del Motor: {__version__}")
    print(f"Estado PM7: {governance['status']}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Cierre arquitectónico: {'APROBADO' if approved else 'RECHAZADO'}")
    print(
        f"Contrato de salida: {governance['output_contract']['name']} "
        f"v{governance['output_contract']['version']}",
    )
    print(f"Preparado para producción: {'SÍ' if approved else 'NO'}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "7.10",
                "prompt_maestro": "7",
                "prompt_maestro_7_status": governance["status"],
                "passed": approved,
                "total_checks": total,
                "passed_checks": passed,
                "governance": governance,
                "checks": [check.to_dict() for check in checks],
            },
            indent=2,
            ensure_ascii=False,
        ),
    )
    return 0 if approved else 1


if __name__ == "__main__":
    sys.exit(main())
