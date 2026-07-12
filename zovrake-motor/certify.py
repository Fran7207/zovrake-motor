"""
Punto de entrada de certificación del Motor Inteligente ZOVRAKE.

Implementación 1.10 — Certificación Arquitectónica del Núcleo.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor.certification import CoreCertificationChecker


def main() -> int:
    report = CoreCertificationChecker().run()

    print("=" * 60)
    print("CERTIFICACIÓN ARQUITECTÓNICA — PROMPT MAESTRO 3")
    print("Implementación 1.10 — Núcleo del Motor Inteligente ZOVRAKE")
    print("=" * 60)
    print(f"Versión del Motor: {report.motor_version}")
    print(f"Verificaciones: {report.passed_checks}/{report.total_checks} aprobadas")
    print(f"Certificación global: {'APROBADA' if report.passed else 'RECHAZADA'}")
    print(
        f"Preparado para Prompt Maestro 4: "
        f"{'SÍ' if report.certified_for_prompt_maestro_4 else 'NO'}"
    )
    print(
        f"Prompt Maestro 4 COMPLETO: "
        f"{'SÍ' if report.certified_prompt_maestro_4_complete else 'NO'}"
    )
    print(
        f"Prompt Maestro 5 COMPLETO: "
        f"{'SÍ' if report.certified_prompt_maestro_5_complete else 'NO'}"
    )
    print(
        f"Prompt Maestro 5 CERRADO: "
        f"{'SÍ' if report.prompt_maestro_5_closed else 'NO'}"
    )
    print(
        f"Prompt Maestro 6 COMPLETO: "
        f"{'SÍ' if report.certified_prompt_maestro_6_complete else 'NO'}"
    )
    print(
        f"Preparado para Prompt Maestro 7: "
        f"{'SÍ' if report.certified_prompt_maestro_6_complete else 'NO'}"
    )
    print("-" * 60)

    if not report.passed:
        for check in report.checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
