"""Gestión del ciclo de vida de coordinación."""

from __future__ import annotations

from datetime import datetime, timezone

from zovrake_motor.coordinator.enums import CoordinationPhase
from zovrake_motor.coordinator.models import CoordinationProcess, PhaseRecord


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LifecycleManager:
    """
    Administra las fases del ciclo de coordinación.

    Solicitud → Inicialización → Coordinación → Procesamiento → Finalización

    En esta etapa recorre las fases sin ejecutar lógica de negocio.
    """

    PHASE_SEQUENCE: tuple[CoordinationPhase, ...] = (
        CoordinationPhase.SOLICITUD,
        CoordinationPhase.INICIALIZACION,
        CoordinationPhase.COORDINACION,
        CoordinationPhase.PROCESAMIENTO,
        CoordinationPhase.FINALIZACION,
    )

    def begin_phase(
        self,
        process: CoordinationProcess,
        phase: CoordinationPhase,
        *,
        message: str = "",
    ) -> PhaseRecord:
        if process.phases and process.phases[-1].completed_at is None:
            process.phases[-1].completed_at = _utc_now()

        record = PhaseRecord(phase=phase, message=message)
        process.phases.append(record)
        process.current_phase = phase
        process.updated_at = _utc_now()
        return record

    def complete_phase(self, process: CoordinationProcess) -> None:
        if process.phases and process.phases[-1].completed_at is None:
            process.phases[-1].completed_at = _utc_now()
        process.updated_at = _utc_now()

    def run_lifecycle(self, process: CoordinationProcess) -> list[CoordinationPhase]:
        """Recorre todas las fases del ciclo sin procesamiento real."""
        completed: list[CoordinationPhase] = []

        for phase in self.PHASE_SEQUENCE:
            self.begin_phase(process, phase, message=f"Fase {phase.value} preparada")
            self.complete_phase(process)
            completed.append(phase)

        process.current_phase = None
        return completed
