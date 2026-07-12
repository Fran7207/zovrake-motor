"""Almacén de mensajes del ECG — memoria, sin colas."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.ecg.messages.models import EcgMessageEnvelope


class EcgMessageStore:
    """Gestiona solicitudes, respuestas, errores y notificaciones en memoria."""

    def __init__(self) -> None:
        self._messages: list[EcgMessageEnvelope] = []

    def append(self, message: EcgMessageEnvelope) -> None:
        self._messages.append(message)

    def by_process(self, process_id: UUID) -> tuple[EcgMessageEnvelope, ...]:
        return tuple(item for item in self._messages if item.process_id == process_id)

    def count(self) -> int:
        return len(self._messages)

    def count_by_process(self, process_id: UUID) -> int:
        return sum(1 for item in self._messages if item.process_id == process_id)

    def snapshot(self) -> list[dict]:
        return [message.to_dict() for message in self._messages]
