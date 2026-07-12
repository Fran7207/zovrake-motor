"""Modelos del módulo de Comunicación."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OutboundMessage:
    """Mensaje de salida hacia el ERP — estructura preparatoria."""

    payload: dict[str, Any] = field(default_factory=dict)
    channel: str = "internal"

    def to_dict(self) -> dict[str, Any]:
        return {"channel": self.channel, "payload": self.payload}
