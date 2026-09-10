"""Orquestador híbrido: ZOVRAKE manda; OpenAI ayuda cuando hace falta."""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any

from .confidence_gate import OpenAIComprehensionGate
from .evidence_selector import ComprehensionEvidenceSelector
from .merger import AIUnderstandingMerger
from .models import AIComprehensionResult, ComprehensionRoute
from .openai_provider import OpenAIComprehensionProvider


class OpenAIComprehensionOrchestrator:
    VERSION = "1.0.0"

    def __init__(
        self,
        *,
        provider: OpenAIComprehensionProvider | None = None,
        gate: OpenAIComprehensionGate | None = None,
        selector: ComprehensionEvidenceSelector | None = None,
    ) -> None:
        self.provider = provider or OpenAIComprehensionProvider()
        self.gate = gate or OpenAIComprehensionGate()
        self.selector = selector or ComprehensionEvidenceSelector()
        self.merger = AIUnderstandingMerger()

    def is_enabled(self) -> bool:
        flag = os.getenv("ZOVRAKE_OPENAI_ENABLED", "auto").strip().lower()
        return flag not in {
            "0", "false", "no", "off", "disabled"
        } and bool(getattr(self.provider, "configured", False))

    def enhance(
        self,
        knowledge,
        *,
        pdf_bytes: bytes | None = None,
    ):
        decision = self.gate.decide(knowledge)
        metadata = dict(getattr(knowledge, "metadata", {}) or {})

        # Internamente conservamos auditoría técnica; la capa web NO debe
        # mostrar estos datos como parte del resultado funcional.
        metadata["openai_hybrid_router"] = {
            **decision.to_dict(),
            "enabled": self.is_enabled(),
            "provider": "openai_responses" if self.is_enabled() else "disabled",
            "version": self.VERSION,
        }

        if decision.route is ComprehensionRoute.LOCAL_ONLY:
            metadata["openai_hybrid_understanding"] = {
                "status": "not_called",
                "route": decision.route.value,
                "reason": "local_confidence_sufficient",
            }
            return replace(knowledge, metadata=metadata)

        if not self.is_enabled():
            metadata["openai_hybrid_understanding"] = {
                "status": "not_called",
                "route": decision.route.value,
                "reason": "provider_not_configured",
            }
            return replace(knowledge, metadata=metadata)

        selected = self.selector.select(
            knowledge,
            decision.route,
            pdf_bytes,
        )
        result: AIComprehensionResult = self.provider.comprehend(
            knowledge=knowledge,
            route=decision.route,
            selected_context=selected,
            pdf_bytes=pdf_bytes,
        )

        metadata["openai_hybrid_understanding"] = {
            "status": "completed" if result.success else "failed",
            "route": result.route.value,
            "model": result.model,
            "cache_hit": result.cache_hit,
            "response_id": result.response_id,
            "input_character_count": result.input_character_count,
            "error": result.error,
            "selected_pages": selected.get("selected_pages", []),
            "selected_image_count": len(
                selected.get("selected_images", []) or []
            ),
            "understanding": result.output,
        }

        if result.success:
            local_understanding = metadata.get(
                "deep_universal_understanding", {}
            ) or {}
            metadata["deep_hybrid_document_understanding"] = (
                self.merger.merge(
                    local_understanding=local_understanding,
                    ai_understanding=result.output,
                )
            )
            metadata["deep_reasoning_source"] = "hybrid_local_openai"
            metadata["hybrid_payment_facts"] = [
                fact
                for fact in result.output.get("facts", [])
                if str(fact.get("attribute", "")).strip().lower()
                in {
                    "payment_method",
                    "payment_terms",
                    "forma_de_pago",
                    "condiciones_de_pago",
                    "payment",
                }
            ]
            metadata["hybrid_numeric_checks"] = list(
                result.output.get("numeric_checks", ()) or ()
            )
            metadata["hybrid_uncertainties"] = list(
                result.output.get("uncertainties", ()) or ()
            )
        else:
            metadata["deep_reasoning_source"] = "local_fallback"

        return replace(knowledge, metadata=metadata)
