"""
Punto de entrada del cierre formal del Prompt Maestro 8.

Implementacion 8.12 — Gobierno arquitectonico de la Plataforma de Integracion Empresarial.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.enterprise_integration_closure_checker import (
    EnterpriseIntegrationModuleClosureChecker,
)
from zovrake_motor.enterprise_integration.governance import closure_snapshot


def main() -> int:
    checks = EnterpriseIntegrationModuleClosureChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total
    governance = closure_snapshot()

    print("=" * 60)
    print("CIERRE FORMAL — PROMPT MAESTRO 8")
    print("Plataforma de Integracion Empresarial — Implementacion 8.12")
    print("=" * 60)
    print(f"Version del Motor: {__version__}")
    print(f"Estado PM8: {governance['status']}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Cierre arquitectonico: {'APROBADO' if approved else 'RECHAZADO'}")
    print(
        f"Contrato oficial: {governance['integration_contract']['name']} "
        f"v{governance['integration_contract']['version']}",
    )
    print(f"Punto de entrada ERP: {governance['integration_contract']['official_entry_point']}")
    print(f"Preparado para produccion: {'SI' if approved else 'NO'}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "8.12",
                "prompt_maestro": "8",
                "prompt_maestro_8_status": governance["status"],
                "passed": approved,
                "total_checks": total,
                "passed_checks": passed,
                "governance": governance,
                "checks": [check.to_dict() for check in checks],
            },
            indent=2,
            ensure_ascii=True,
        ),
    )
    return 0 if approved else 1


if __name__ == "__main__":
    sys.exit(main())
