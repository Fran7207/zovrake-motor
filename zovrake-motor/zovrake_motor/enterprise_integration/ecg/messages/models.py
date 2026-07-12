"""Modelos de mensajes del ECG."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.ecg.enums import EcgChannelDirection, EcgMessageType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EcgMessageEnvelope:
    """Sobre de mensaje — preparado para colas futuras, sin persistencia en 8.4."""

    message_id: str
    process_id: UUID
    message_type: EcgMessageType
    direction: EcgChannelDirection
    payload: dict[str, Any]
    occurred_at: datetime = field(default_factory=utc_now)
    immutable: bool = True

    @classmethod
    def create(
        cls,
        *,
        process_id: UUID,
        message_type: EcgMessageType,
        direction: EcgChannelDirection,
        payload: dict[str, Any],
    ) -> EcgMessageEnvelope:
        return cls(
            message_id=str(uuid4()),
            process_id=process_id,
            message_type=message_type,
            direction=direction,
            payload=payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "process_id": str(self.process_id),
            "message_type": self.message_type.value,
            "direction": self.direction.value,
            "payload": self.payload,
            "occurred_at": self.occurred_at.isoformat(),
            "immutable": self.immutable,
        }
