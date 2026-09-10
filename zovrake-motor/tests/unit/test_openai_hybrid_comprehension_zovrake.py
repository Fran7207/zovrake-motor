from zovrake_motor.comprehension.ai.confidence_gate import (
    OpenAIComprehensionGate,
)
from zovrake_motor.comprehension.ai.models import (
    ComprehensionRoute,
)
from zovrake_motor.comprehension.ai.orchestrator import (
    OpenAIComprehensionOrchestrator,
)
from zovrake_motor.comprehension.models import DocumentKnowledge


class FakeProvider:
    model = "gpt-5.6-luna"
    configured = True

    def comprehend(self, *, knowledge, route, selected_context, pdf_bytes=None):
        from zovrake_motor.comprehension.ai.models import AIComprehensionResult

        return AIComprehensionResult(
            success=True,
            route=route,
            model=self.model,
            output={
                "document_type": "quotation",
                "summary": "demo",
                "entities": [],
                "facts": [
                    {
                        "subject": "document",
                        "attribute": "payment_method",
                        "value": "Contado",
                        "normalized_value": "contado",
                        "value_type": "text",
                        "confidence": 0.99,
                        "evidence_refs": ["e1"],
                    }
                ],
                "relationships": [],
                "sections": [],
                "items": [],
                "visual_observations": [],
                "numeric_checks": [],
                "uncertainties": [],
            },
        )


def test_small_resolved_document_stays_local():
    knowledge = DocumentKnowledge(
        document_id="d",
        page_count=1,
        text="Proveedor: Demo",
        metadata={
            "deep_universal_understanding": {
                "resolved_roles": [{"role": "provider", "decision": "resolved"}]
            }
        },
    )
    assert (
        OpenAIComprehensionGate().decide(knowledge).route
        is ComprehensionRoute.LOCAL_ONLY
    )


def test_orchestrator_enriches_without_replacing_local_knowledge():
    knowledge = DocumentKnowledge(
        document_id="d",
        file_name="demo.pdf",
        page_count=2,
        text="Proveedor?\nForma de pago: Contado",
        unresolved=(
            {"type": "ambiguous"},
            {"type": "ambiguous"},
            {"type": "ambiguous"},
        ),
        images=(
            {"page_number": 1},
            {"page_number": 1},
            {"page_number": 2},
            {"page_number": 2},
        ),
    )
    result = OpenAIComprehensionOrchestrator(
        provider=FakeProvider()
    ).enhance(knowledge, pdf_bytes=b"%PDF-demo")
    assert result.metadata["deep_reasoning_source"] == "hybrid_local_openai"
    assert result.metadata["deep_hybrid_document_understanding"]["ai_facts"][0]["value"] == "Contado"
