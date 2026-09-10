"""Modelos internos de la capa híbrida de comprensión de ZOVRAKE."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComprehensionRoute(str, Enum):
    """Nivel mínimo de ayuda remota necesario."""

    LOCAL_ONLY = "local_only"
    SELECTED_EVIDENCE = "selected_evidence"
    FULL_PDF = "full_pdf"


@dataclass(frozen=True)
class GateDecision:
    route: ComprehensionRoute
    score: float
    reasons: tuple[str, ...] = ()

    @property
    def estimated_calls(self) -> int:
        return 0 if self.route is ComprehensionRoute.LOCAL_ONLY else 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "route": self.route.value,
            "score": self.score,
            "reasons": list(self.reasons),
            "estimated_calls": self.estimated_calls,
        }


@dataclass(frozen=True)
class AIComprehensionResult:
    success: bool
    route: ComprehensionRoute
    model: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    cache_hit: bool = False
    response_id: str = ""
    error: str = ""
    input_character_count: int = 0

    @property
    def usable(self) -> bool:
        return self.success and bool(self.output)
